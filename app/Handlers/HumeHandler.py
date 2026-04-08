from dotenv import load_dotenv
import os
import requests
import time

load_dotenv()


class HumeHandler:
    def __init__(self):
        self.api_key = os.getenv('HUME_API_KEY')
        self.base_url = "https://api.hume.ai/v0/batch"

    def analyze_audio(self, audio_bytes: bytes, filename: str = "audio.ogg") -> dict:
        headers = {"X-Hume-Api-Key": self.api_key}

        # Enviar el archivo para análisis
        files = {"file": (filename, audio_bytes, "audio/ogg")}
        data = {"models": '{"prosody": {}}'}
        response = requests.post(f"{self.base_url}/jobs", headers=headers, files=files, data=data)

        if response.status_code != 200:
            raise Exception(f"Error Hume submit: {response.status_code} - {response.text}")

        job_id = response.json()["job_id"]

        # Esperar resultados (máx 30 segundos)
        for _ in range(15):
            time.sleep(2)
            result = requests.get(f"{self.base_url}/jobs/{job_id}/predictions", headers=headers)
            if result.status_code == 200:
                return self._extract_top_emotions(result.json())

        raise Exception("Hume timeout: el análisis tardó demasiado")

    def _extract_top_emotions(self, predictions: list) -> dict:
        try:
            emotions = (
                predictions[0]["results"]["predictions"][0]
                ["models"]["prosody"]["grouped_predictions"][0]
                ["predictions"][0]["emotions"]
            )
            top = sorted(emotions, key=lambda x: x["score"], reverse=True)[:3]
            return {e["name"]: round(e["score"], 2) for e in top}
        except Exception:
            return {}
