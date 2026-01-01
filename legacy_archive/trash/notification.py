import requests
import json
import config

class EmailNotification:
    def __init__(self):
        self.api_url = "https://api.emailjs.com/api/v1.0/email/send"

    def send_email(self, subject, message_body):
        """
        Sends an email using EmailJS REST API.
        """
        data = {
            "service_id": config.EMAILJS_SERVICE_ID,
            "template_id": config.EMAILJS_TEMPLATE_ID,
            "user_id": config.EMAILJS_PUBLIC_KEY, # In EmailJS API 'user_id' acts as Public Key
            # Note: For strict security, private keys shouldn't be exposed easily, 
            # but EmailJS client-side often uses just public key. 
            # If the user provided a Private Key, it usually implies using server-side SDK 
            # or adding 'accessToken' in the payload if 'Private Key' is actually the 'Access Token'.
            # Based on standard EmailJS Python usage via REST:
            "template_params": {
                "to_email": config.EMAILJS_USER_EMAIL,
                "subject": subject,
                "message": message_body
            }
        }
        
        # If the private key is intended as the accessToken (which is common for server-side)
        if hasattr(config, 'EMAILJS_PRIVATE_KEY') and config.EMAILJS_PRIVATE_KEY:
             data['accessToken'] = config.EMAILJS_PRIVATE_KEY

        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(self.api_url, data=json.dumps(data), headers=headers)
            if response.status_code == 200 or response.text == 'OK':
                print(f"Email sent successfully: {subject}")
                print(f"Response: {response.text}")
                return True
            else:
                print(f"Failed to send email. Status Code: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

if __name__ == "__main__":
    # Test
    notifier = EmailNotification()
    notifier.send_email("Test Subject", "This is a test notification from the trading bot.")
