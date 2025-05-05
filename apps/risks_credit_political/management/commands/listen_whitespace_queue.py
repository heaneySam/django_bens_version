import logging
import time
import json
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from azure.servicebus import ServiceBusClient, ServiceBusMessage, ServiceBusReceiver
from azure.core.exceptions import ServiceRequestError
from apps.risks_credit_political.models import CreditPoliticalRisk

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Command(BaseCommand):
    help = 'Listens to the Azure Service Bus queue for Whitespace quote requests and creates risk entries.'

    def handle(self, *args, **options):
        required_settings = [
            'WHITESPACE_API_BASE_URL',
            'WHITESPACE_AUTH_TOKEN',
            'AZURE_SERVICE_BUS_CONNECTION_STRING',
            'WHITESPACE_QUEUE_NAME',
        ]

        missing_settings = [s for s in required_settings if not hasattr(settings, s) or not getattr(settings, s)]
        if missing_settings:
            logger.error(f"Missing required settings: {', '.join(missing_settings)}")
            self.stderr.write(self.style.ERROR(f"Missing required settings: {', '.join(missing_settings)}"))
            return

        conn_str = settings.AZURE_SERVICE_BUS_CONNECTION_STRING
        queue_name = settings.WHITESPACE_QUEUE_NAME
        api_base_url = settings.WHITESPACE_API_BASE_URL
        api_token = settings.WHITESPACE_AUTH_TOKEN

        logger.info(f"Starting listener for queue: {queue_name}")
        self.stdout.write(self.style.SUCCESS(f"Starting listener for queue: {queue_name}"))

        while True:
            try:
                with ServiceBusClient.from_connection_string(conn_str=conn_str) as client:
                    with client.get_queue_receiver(queue_name=queue_name) as receiver:
                        logger.info("Receiver connected. Waiting for messages...")
                        received_msgs = receiver.receive_messages(max_wait_time=10) # Wait up to 10 seconds for messages

                        if not received_msgs:
                            # No messages, continue loop to check again
                            continue

                        for msg in received_msgs:
                            try:
                                logger.info(f"Received message: {msg.message_id}")
                                body_str = str(msg)
                                body_json = json.loads(body_str)

                                activity = body_json.get('hardcodedActivity')
                                parent_doc_id = body_json.get('parentDocID')

                                if activity == 'Quote Requested' and parent_doc_id:
                                    logger.info(f"Processing 'Quote Requested' for doc ID: {parent_doc_id}")
                                    self.process_quote_request(parent_doc_id, api_base_url, api_token, receiver, msg)
                                else:
                                    logger.warning(f"Skipping message {msg.message_id}: Not a 'Quote Requested' event or missing parentDocID.")
                                    # For non-relevant messages, we still complete them
                                    receiver.complete_message(msg)

                            except json.JSONDecodeError:
                                logger.error(f"Failed to decode JSON for message {msg.message_id}: {body_str}")
                                receiver.dead_letter_message(msg, reason="JSONDecodeError", error_description="Could not parse message body as JSON.")
                            except Exception as e:
                                logger.exception(f"Error processing message {msg.message_id}: {e}")
                                try:
                                    # Attempt to abandon for potential retry
                                    receiver.abandon_message(msg)
                                except Exception as abandon_exc:
                                    logger.error(f"Failed to abandon message {msg.message_id}: {abandon_exc}")
                                    # If abandon fails, maybe dead-letter? Requires careful consideration.

            except ServiceRequestError as e:
                logger.error(f"Azure Service Bus connection error: {e}. Retrying in 60 seconds...")
                time.sleep(60)
            except KeyboardInterrupt:
                logger.info("Listener stopped manually.")
                self.stdout.write(self.style.WARNING("Listener stopped manually."))
                break
            except Exception as e:
                logger.exception(f"An unexpected error occurred in the main loop: {e}. Retrying in 60 seconds...")
                time.sleep(60) # Wait before retrying the connection/loop

    def process_quote_request(self, quote_request_id, api_base_url, api_token, receiver, msg):
        """Fetches risk details from Whitespace API and saves to the database."""
        api_url = f"{api_base_url}/api/risks/{quote_request_id}"
        headers = {
            'Authorization': f'Bearer {api_token}',
            'Accept': 'application/json'
        }

        try:
            logger.info(f"Fetching data from Whitespace API: {api_url}")
            response = requests.get(api_url, headers=headers, timeout=30) # 30 second timeout
            response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)

            risk_data = response.json()
            logger.info(f"Successfully fetched data for {quote_request_id}")

            # Use update_or_create to prevent duplicates and handle retries
            risk_instance, created = CreditPoliticalRisk.objects.update_or_create(
                source_system="Whitespace",
                source_record_id=quote_request_id,
                defaults={'unstructured_data': risk_data}
            )

            if created:
                logger.info(f"Created new CreditPoliticalRisk record for {quote_request_id}")
                self.stdout.write(self.style.SUCCESS(f"Created risk: {quote_request_id}"))
            else:
                logger.info(f"Updated existing CreditPoliticalRisk record for {quote_request_id}")
                self.stdout.write(self.style.SUCCESS(f"Updated risk: {quote_request_id}"))

            # Important: Complete the message only after successful processing
            receiver.complete_message(msg)
            logger.info(f"Completed message {msg.message_id}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch data from Whitespace API for {quote_request_id}: {e}")
            # Abandon the message so it can be retried later
            try:
                receiver.abandon_message(msg)
                logger.info(f"Abandoned message {msg.message_id} due to API fetch error.")
            except Exception as abandon_exc:
                logger.error(f"Failed to abandon message {msg.message_id} after API fetch error: {abandon_exc}")
        except Exception as e:
            logger.exception(f"Failed to process or save risk data for {quote_request_id}: {e}")
            # For database errors or other unexpected issues, abandon for retry
            try:
                receiver.abandon_message(msg)
                logger.info(f"Abandoned message {msg.message_id} due to processing error.")
            except Exception as abandon_exc:
                logger.error(f"Failed to abandon message {msg.message_id} after processing error: {abandon_exc}") 