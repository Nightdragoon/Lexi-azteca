from dotenv import load_dotenv, set_key
import os
import requests

load_dotenv()


class TelegramHandler:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def update_token(self, new_token: str):
        """Actualiza el token en memoria y en el archivo .env"""
        self.token = new_token
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        set_key(env_path, 'TELEGRAM_TOKEN', new_token)

    def send_message(self, chat_id: int, text: str):
        """Envía un mensaje de texto a un chat de Telegram"""
        payload = {
            "chat_id": chat_id,
            "text": text
        }
        response = requests.post(f"{self.base_url}/sendMessage", json=payload)
        if response.status_code == 200:
            return response.json()
        raise Exception(f"Error Telegram API: {response.status_code} - {response.text}")

    def set_webhook(self, url: str):
        """Registra el webhook en Telegram"""
        payload = {"url": url}
        response = requests.post(f"{self.base_url}/setWebhook", json=payload)
        if response.status_code == 200:
            return response.json()
        raise Exception(f"Error Telegram API: {response.status_code} - {response.text}")

    def delete_webhook(self):
        """Elimina el webhook registrado"""
        response = requests.post(f"{self.base_url}/deleteWebhook")
        if response.status_code == 200:
            return response.json()
        raise Exception(f"Error Telegram API: {response.status_code} - {response.text}")
