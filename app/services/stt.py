import io
import asyncio
from groq import Groq
from app.config import settings

class STTService:
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)

    async def transcribe(self, audio_bytes: bytes, audio_format: str = None) -> str:
        """Transcribe audio bytes using Groq Whisper."""
        if audio_format is None:
            audio_format = settings.audio_format

        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = f"audio.{audio_format}"   # e.g., audio.webm

        response = await asyncio.to_thread(
            self.client.audio.transcriptions.create,
            model=settings.stt_model,
            file=audio_file,
            response_format="text"
        )
        return response