from dotenv import load_dotenv
import os
import requests

class AIHandler:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.api_url = "https://api.deepseek.com/chat/completions"
        self.model = "deepseek-chat"  # o "deepseek-reasoner" para el modelo R1

    def generate_response(self, prompt, user_context: dict = None):
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        messages = []

        if user_context:
            context_lines = "\n".join(f"{k}: {v}" for k, v in user_context.items())
            messages.append({
                "role": "system",
                "content": f"Datos del usuario con el que estás hablando:\n{context_lines}"
            })

        messages.append({"role": "user", "content": prompt , "personalidad": "eres un asistente de finanzas llamado lexi azteca , estas dirigido a jovenes de entre 18 a 25 años , fuiste creado por el stem fesc "})

        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 150
        }
        response = requests.post(self.api_url, headers=headers, json=data)

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception(f"Error en la API: {response.status_code} - {response.text}")