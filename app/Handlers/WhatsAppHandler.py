from dotenv import load_dotenv, set_key
import os
import requests


class WhatsAppHandler:
    def __init__(self):
        load_dotenv()
        self.token = os.getenv('WHATSAPP_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.api_version = os.getenv('WHATSAPP_API_VERSION', 'v23.0')
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"

    def _headers(self):
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

    def update_token(self, new_token: str):
        """Actualiza el token en memoria y en el archivo .env"""
        self.token = new_token
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        set_key(env_path, 'WHATSAPP_TOKEN', new_token)

    def send_template(self, to: str, template_name: str, language_code: str = 'en_US'):
        """Envía un mensaje de plantilla (template) de WhatsApp"""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code}
            }
        }
        response = requests.post(self.base_url, headers=self._headers(), json=payload)
        if response.status_code == 200:
            return response.json()
        raise Exception(f"Error WhatsApp API: {response.status_code} - {response.text}")

    def send_text(self, to: str, message: str):
        """Envía un mensaje de texto libre a un número de WhatsApp"""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        response = requests.post(self.base_url, headers=self._headers(), json=payload)
        if response.status_code == 200:
            return response.json()
        raise Exception(f"Error WhatsApp API: {response.status_code} - {response.text}")
