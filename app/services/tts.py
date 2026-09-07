import os
import asyncio
import tempfile
import edge_tts
from app.config import settings

class TTSService:
    def __init__(self):
        self.lock = asyncio.Lock()

    def get_voice(self, text: str) -> str:
        """Return Arabic voice if text contains Arabic characters, else English voice."""
        # Check for Arabic Unicode range
        if any('\u0600' <= char <= '\u06FF' for char in text):
            return settings.tts_voice_arabic
        return settings.tts_voice_english

    async def synthesize(self, text: str) -> bytes:
        voice = self.get_voice(text)
        async with self.lock:
            communicate = edge_tts.Communicate(text, voice=voice)
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                await communicate.save(tmp_path)
                with open(tmp_path, "rb") as f:
                    audio_bytes = f.read()
            finally:
                os.unlink(tmp_path)
            return audio_bytes

    async def stream_synthesize(self, text: str):
        voice = self.get_voice(text)
        async with self.lock:
            communicate = edge_tts.Communicate(text, voice=voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]