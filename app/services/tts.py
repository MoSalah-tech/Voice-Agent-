import os
import asyncio
import tempfile
import edge_tts
from app.config import settings

class TTSService:
    def __init__(self):
        self.lock = asyncio.Lock()   # serialize TTS calls





    async def stream_synthesize(self, text):
        communicate = edge_tts.Communicate(text, voice=settings.tts_voice)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]  

    async def synthesize(self, text: str) -> bytes:
        """Convert text to MP3 using Edge TTS and return bytes."""
        async with self.lock:
            communicate = edge_tts.Communicate(text, voice=settings.tts_voice)
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                await communicate.save(tmp_path)
                with open(tmp_path, "rb") as f:
                    audio_bytes = f.read()
            finally:
                os.unlink(tmp_path)
            return audio_bytes