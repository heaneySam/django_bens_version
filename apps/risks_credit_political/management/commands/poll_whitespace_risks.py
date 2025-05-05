import logging
import time
import json
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.risks_credit_political.models import CreditPoliticalRisk

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

        logger.info(f"Starting Whitespace poller. Interval: {POLLING_INTERVAL_SECONDS} seconds.")
        self.stdout.write(self.style.SUCCESS(f"Starting Whitespace poller. Interval: {POLLING_INTERVAL_SECONDS} seconds."))

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
                    self.fetch_and_save_risk_details(quote_request_id, api_base_url, headers)

            except requests.exceptions.RequestException as e:
                logger.error(f"Error polling Whitespace API: {e}")
            except Exception as e:
                logger.exception(f"An unexpected error occurred in the polling loop: {e}")
            
            # Wait for the next polling interval
            logger.info(f"Waiting {POLLING_INTERVAL_SECONDS} seconds for next poll...")
            time.sleep(POLLING_INTERVAL_SECONDS)

    def fetch_and_save_risk_details(self, quote_request_id, api_base_url, headers):
        """Fetches full details for a specific risk ID and saves it."""
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

            risk_instance, created = CreditPoliticalRisk.objects.update_or_create(
                source_system="Whitespace",
                source_record_id=quote_request_id,
                defaults={
                    'unstructured_data': risk_data,
                    'created_by_id': system_user.pk # Assign the system user's ID
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

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch details for {quote_request_id}: {e}")
            # Keep polling, maybe it will succeed next time
        except User.DoesNotExist:
             logger.error("Failed to find a system user (superuser). Cannot save record.")
        except Exception as e:
            logger.exception(f"Failed to process or save details for {quote_request_id}: {e}")
            # Keep polling 