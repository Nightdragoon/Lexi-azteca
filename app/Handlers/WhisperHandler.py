from dotenv import load_dotenv
import os
import requests

load_dotenv()


class WhisperHandler:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.url = "https://api.openai.com/v1/audio/transcriptions"

    def transcribe(self, audio_bytes: bytes, filename: str = "audio.ogg") -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        files = {"file": (filename, audio_bytes, "audio/ogg")}
        data = {"model": "whisper-1", "language": "es"}
        response = requests.post(self.url, headers=headers, files=files, data=data)
        if response.status_code == 200:
            return response.json()["text"]
        raise Exception(f"Error Whisper: {response.status_code} - {response.text}")
