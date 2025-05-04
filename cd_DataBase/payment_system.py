import mollie.api.client
import webbrowser
from flask import Flask, request

class PaymentSystem:
    def __init__(self):
        # Initialize Mollie API client
        self.mollie_client = mollie.api.client.Client()
        self.mollie_client.set_api_key("test_vRGRRUDH5QKqasuMKg8fNrU3Jux7pP")  # Replace with your Mollie API key
        self.invoice_status_callback = None  # Callback to update invoice status in GUI

    def create_payment(self, amount, invoice_id, redirect_url, webhook_url):
        """
        Create a payment in Mollie and return the payment URL.
        """
        try:
            # Create the payment with Mollie
            payment = self.mollie_client.payments.create({
                'amount': {
                    'currency': 'EUR',
                    'value': f'{amount:.2f}',  # Format amount as a string
                },
                'description': f'Invoice {invoice_id}',
                'redirectUrl': redirect_url,  # URL for successful payment
                'webhookUrl': webhook_url,   # Webhook URL for status updates
            })
    
            # Log the full payment response for debugging
            print(f"Payment Response: {payment}")
    
            # Safely extract the checkout URL
            if payment and payment["_links"] and payment["_links"].get("checkout"):
                return payment["_links"]["checkout"]["href"]  # Return payment checkout URL
            else:
                print("Error: Checkout link is missing in the Mollie API response.")
                return None
    
        except KeyError as ke:
            print(f"KeyError: {ke}. Mollie API response might be missing fields.")
        except Exception as e:
            print(f"Unexpected Error: {e}")
        return None



    def open_payment_page(self, payment_url):
        """
        Open the payment page in the default browser.
        """
        if payment_url:
            webbrowser.open(payment_url)
        else:
            print("Invalid payment URL.")

    def start_webhook_server(self, host="0.0.0.0", port=5000):
        """
        Start a Flask webhook server to handle Mollie's notifications.
        """
        app = Flask(__name__)

        @app.route('/webhook', methods=['POST'])
        def webhook():
            """
            Handle payment status updates from Mollie.
            """
            data = request.json
            payment_id = data['id']

            try:
                # Get payment details
                payment = self.mollie_client.payments.get(payment_id)

                # Determine payment status
                status = payment['status']
                print(f"Payment {payment_id} status: {status}")

                # Update invoice status in GUI (if callback is defined)
                if self.invoice_status_callback:
                    self.invoice_status_callback(status)

            except Exception as e:
                print(f"Error processing webhook: {e}")

            return '', 200

        print(f"Starting webhook server on {host}:{port}")
        app.run(host=host, port=port)

    def set_invoice_status_callback(self, callback):
        """
        Set a callback function to update the invoice status in the GUI.
        """
        self.invoice_status_callback = callback
