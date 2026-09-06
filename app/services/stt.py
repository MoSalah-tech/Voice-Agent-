import io
import asyncio
from groq import Groq
from app.config import settings

class STTService:
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)

    async def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe audio bytes using Groq Whisper."""
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav"  # change if using other formats
        response = await asyncio.to_thread(
            self.client.audio.transcriptions.create,
            model=settings.stt_model,
            file=audio_file,
            response_format="text"
        )
        return response