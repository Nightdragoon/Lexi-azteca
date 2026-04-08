from dotenv import load_dotenv
import os
import requests

load_dotenv()


class ElevenLabsHandler:
    def __init__(self):
        self.api_key = os.getenv('ELEVENLABS_API_KEY')
        self.voice_id = os.getenv('ELEVENLABS_VOICE_ID', 'cgSgspJ2msm6clMCkdW9')  # voz por defecto (Jessica)
        self.url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"

    def text_to_speech(self, text: str) -> bytes:
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        response = requests.post(self.url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.content
        raise Exception(f"Error ElevenLabs: {response.status_code} - {response.text}")
