import os 
import tempfile
import edge_tts
from app.config import settings

class TTSService:
    async def synthesize(self , text: str)->bytes:
        communicate = edge_tts.Communicate(text, voice = settings.tts_voice)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            await communicate.save(tmp.name)
            tmp_path = tmp.name
        try:
            await communicate.save(tmp_path)
            with open(tmp_path , "rb") as f:
                audio_bytes = f.read()
        finally:
            os.unlink(tmp_path)
        return audio_bytes    
