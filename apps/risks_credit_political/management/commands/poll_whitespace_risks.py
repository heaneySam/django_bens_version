import logging
import time
import json
import requests
import boto3
from botocore.exceptions import ClientError
from io import BytesIO
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.files import File
from django.db import connection
from apps.risks_credit_political.models import CreditPoliticalRisk
from apps.attachments_risks.models import Attachment
import os

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration --- 
POLLING_INTERVAL_SECONDS = 300 # Poll every 5 minutes
API_TIMEOUT_SECONDS = 30

class Command(BaseCommand):
    help = 'Periodically polls Whitespace API for new quote requests and saves them to the database.'

    def handle(self, *args, **options):
        required_settings = [
            'WHITESPACE_API_BASE_URL',
            'WHITESPACE_AUTH_TOKEN',
            'AWS_STORAGE_BUCKET_NAME'
        ]

        missing_settings = [s for s in required_settings if not hasattr(settings, s) or not getattr(settings, s)]
        if missing_settings:
            logger.error(f"Missing required settings: {', '.join(missing_settings)}")
            self.stderr.write(self.style.ERROR(f"Missing required settings: {', '.join(missing_settings)}"))
            return

        api_base_url = settings.WHITESPACE_API_BASE_URL
        api_token = settings.WHITESPACE_AUTH_TOKEN
        headers = {
            'Authorization': f'Bearer {api_token}',
            'Accept': 'application/json'
        }

        s3_bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        s3_client = boto3.client('s3')

        logger.info(f"Starting Whitespace poller. Interval: {POLLING_INTERVAL_SECONDS} seconds. Using S3 bucket: {s3_bucket_name}")
        self.stdout.write(self.style.SUCCESS(f"Starting Whitespace poller. Interval: {POLLING_INTERVAL_SECONDS} seconds. Using S3 bucket: {s3_bucket_name}"))

        while True:
            try:
                logger.info("Polling Whitespace for risks...")
                
                # --- Step 1: Fetch list of risks/quote requests --- 
                # NOTE: This assumes /api/risks returns a list of objects, each having an 'id' field.
                # Adjust the URL and response parsing based on the actual Whitespace API endpoint.
                # Consider adding parameters like ?status=QuoteRequested or date filters if available.
                list_api_url = f"{api_base_url}/api/risks"
                response = requests.get(list_api_url, headers=headers, timeout=API_TIMEOUT_SECONDS)
                response.raise_for_status()
                all_risks_list = response.json() # Assumes response is a JSON list like [{'id': '...', ...}, ...]
                
                if not isinstance(all_risks_list, list):
                     logger.error(f"Unexpected response format from {list_api_url}. Expected a list, got {type(all_risks_list)}")
                     time.sleep(POLLING_INTERVAL_SECONDS)
                     continue

                # Extract potential quote request IDs (adjust logic if needed)
                potential_quote_request_ids = set()
                for risk_summary in all_risks_list:
                    risk_id = risk_summary.get('id') # Adjust key if needed
                    # Basic filtering: Check if ID looks like a quote request
                    # More robust filtering might involve checking a 'status' or 'type' field if available in the summary
                    if risk_id and "::QR" in risk_id: 
                        potential_quote_request_ids.add(risk_id)
                
                logger.info(f"Found {len(potential_quote_request_ids)} potential quote requests from API.")

                # --- Step 2: Find which ones are new --- 
                existing_ids = set(
                    CreditPoliticalRisk.objects.filter(
                        source_system="Whitespace", 
                        source_record_id__in=potential_quote_request_ids
                    ).values_list('source_record_id', flat=True)
                )
                
                new_ids = potential_quote_request_ids - existing_ids
                logger.info(f"Found {len(new_ids)} new quote requests to process.")

                # --- Step 3: Process new quote requests --- 
                for quote_request_id in new_ids:
                    self.fetch_and_save_risk_details(quote_request_id, api_base_url, headers, s3_client, s3_bucket_name)

            except requests.exceptions.RequestException as e:
                logger.error(f"Error polling Whitespace API: {e}")
            except Exception as e:
                logger.exception(f"An unexpected error occurred in the polling loop: {e}")
            finally:
                # Ensure the database connection is closed after each cycle
                # to prevent timeouts in long-running commands.
                connection.close()
            
            # Wait for the next polling interval
            logger.info(f"Waiting {POLLING_INTERVAL_SECONDS} seconds for next poll...")
            time.sleep(POLLING_INTERVAL_SECONDS)

    def fetch_and_save_risk_details(self, quote_request_id, api_base_url, headers, s3_client, s3_bucket_name):
        """Fetches full details for a specific risk ID, downloads attachments to S3, and saves it."""
        detail_api_url = f"{api_base_url}/api/risks/{quote_request_id}"
        try:
            # --- Get a system user ---
            User = get_user_model()
            system_user = User.objects.filter(is_superuser=True).order_by('pk').first()
            if not system_user:
                logger.error("No superuser found to assign as created_by. Please create a superuser.")
                # Optionally, raise an exception or handle differently
                return # Skip saving if no system user

            logger.info(f"Fetching details for new risk: {quote_request_id} from {detail_api_url}")
            response = requests.get(detail_api_url, headers=headers, timeout=API_TIMEOUT_SECONDS)
            response.raise_for_status()
            risk_data = response.json()

            # --- Process Attachments --- 
            # REMOVED: processed_attachments_metadata = [] # This variable is no longer used
            # REMOVED: root_id = quote_request_id.split('::')[0] # Moved this logic lower
            # REMOVED: if root_id: # Moved this logic lower
            # REMOVED:     processed_attachments_metadata = self.process_whitespace_attachments(
            # REMOVED:         root_id,
            # REMOVED:         api_base_url,
            # REMOVED:         headers,
            # REMOVED:         s3_client,
            # REMOVED:         s3_bucket_name
            # REMOVED:     )
            # REMOVED: else:
            # REMOVED:     logger.warning(f"Could not extract root_id from {quote_request_id} to fetch attachments.")
            # --- End Process Attachments ---

            risk_instance, created = CreditPoliticalRisk.objects.update_or_create(
                source_system="Whitespace",
                source_record_id=quote_request_id,
                defaults={
                    'unstructured_data': risk_data,
                    'created_by_id': system_user.pk,
                    # 'attachment_metadata': processed_attachments_metadata # REMOVED - Handled by Attachment model now
                    # Optionally add 'updated_by_id': system_user.pk if you have that field too
                }
            )

            if created:
                logger.info(f"Successfully created record for {quote_request_id}")
                self.stdout.write(self.style.SUCCESS(f"Created risk record: {quote_request_id}"))
            else:
                # This shouldn't happen if our new_ids logic is correct, but handle defensively
                logger.warning(f"Updated existing record for {quote_request_id} during detail fetch (unexpected)." )
                self.stdout.write(self.style.WARNING(f"Updated risk record: {quote_request_id}"))

            # --- Process and Save Attachments AFTER Risk is Saved ---
            # Extract root_id again here, or pass it down if needed
            root_id = quote_request_id.split('::')[0]
            if root_id:
                 # Corrected call: Removed assignment and added all args
                 self.process_whitespace_attachments( 
                     root_id=root_id,
                     risk_instance=risk_instance, 
                     system_user=system_user,     
                     api_base_url=api_base_url,
                     headers=headers,
                     s3_client=s3_client,         
                     s3_bucket_name=s3_bucket_name 
                 )
            else:
                 logger.warning(f"Could not extract root_id from {quote_request_id} to fetch attachments.")
            # --- End Attachment Processing ---

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch details for {quote_request_id}: {e}")
            # Keep polling, maybe it will succeed next time
        except User.DoesNotExist:
             logger.error("Failed to find a system user (superuser). Cannot save record.")
        except Exception as e:
            logger.exception(f"Failed to process or save details for {quote_request_id}: {e}")
            # Keep polling 

    def process_whitespace_attachments(self, root_id, risk_instance, system_user, api_base_url, headers, s3_client, s3_bucket_name):
        """Fetches attachment metadata, downloads content, and saves using the Attachment model."""
        metadata_api_url = f"{api_base_url}/api/attachments/{root_id}"
        
        try:
            logger.info(f"Fetching attachment metadata for root_id: {root_id} (Risk ID: {risk_instance.id}) from {metadata_api_url}")
            meta_response = requests.get(metadata_api_url, headers=headers, timeout=API_TIMEOUT_SECONDS)
            meta_response.raise_for_status()
            attachments_info = meta_response.json()

            if not isinstance(attachments_info, list):
                logger.warning(f"Unexpected attachment metadata format for {root_id}. Expected list, got {type(attachments_info)}. Skipping attachments.")
                return

            logger.info(f"Found {len(attachments_info)} attachments for root_id: {root_id}")

            for attachment_info in attachments_info:
                parent_doc_id = attachment_info.get('parentDocID')
                identifier = attachment_info.get('identifier')
                attachment_name = attachment_info.get('attachmentName', 'unknown_attachment')
                content_type = attachment_info.get('content_type', 'application/octet-stream')
                original_size = attachment_info.get('length') # Keep for potential future use

                if not parent_doc_id or not identifier:
                    logger.warning(f"Skipping attachment due to missing parentDocID or identifier for root_id {root_id}: {attachment_info}")
                    continue

                # --- Download Content ---
                content_api_url = f"{api_base_url}/api/attachments/{parent_doc_id}/{identifier}"
                try:
                    logger.info(f"Downloading attachment: {attachment_name} ({identifier}) for Risk ID {risk_instance.id} from {content_api_url}")
                    content_response = requests.get(content_api_url, headers=headers, timeout=API_TIMEOUT_SECONDS, stream=True)
                    content_response.raise_for_status()

                    # --- Create Attachment record and Save File --- 
                    # The save() method on the FileField handles the upload to S3 via risk_attachment_path
                    try:
                        # FileField needs a name for the save() method, 
                        # but risk_attachment_path generates the final storage path.
                        # Use the original filename or a temporary unique name.
                        _, ext = os.path.splitext(attachment_name)
                        temp_filename = f"{identifier}{ext}" # Temporary name for the save method

                        attachment = Attachment(
                            risk=risk_instance,
                            uploaded_by=system_user,
                            original_filename=attachment_name,
                            description=f"Downloaded from Whitespace (Identifier: {identifier})",
                            content_type=content_type
                        )
                        # Create a Django File object from the downloaded content
                        django_file = File(BytesIO(content_response.content), name=temp_filename)
                        
                        # Save the attachment instance. This triggers the upload.
                        attachment.file = django_file # Assign the file object
                        attachment.save() # Save the model instance and the file
                        
                        logger.info(f"Successfully created Attachment record and uploaded file for {attachment_name} (Risk ID: {risk_instance.id}) to {attachment.file.name}")

                    except Exception as e:
                        logger.exception(f"Failed to create Attachment or upload file for {attachment_name} (Risk ID: {risk_instance.id}): {e}")
                    # --- End Create Attachment --- 
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Failed to download attachment content for {identifier} ({attachment_name}) Risk ID {risk_instance.id}: {e}")
                except Exception as e:
                     logger.exception(f"An unexpected error occurred during attachment download for {identifier} ({attachment_name}) Risk ID {risk_instance.id}: {e}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch attachment metadata for {root_id} (Risk ID: {risk_instance.id}): {e}")
            # Proceed without attachments if metadata fails
        except Exception as e:
            logger.exception(f"An unexpected error occurred processing attachments for {root_id} (Risk ID: {risk_instance.id}): {e}")
            # Proceed without attachments 