import json
import redis.asyncio as redis
from typing import List, Dict
from app.config import settings

class MemoryService:
    def __init__(self):
        self.redis = redis.from_url(settings.redis_url, decode_responses=True)

    async def get_history(self, session_id: str) -> List[Dict[str, str]]:
        key = f"conversation:{session_id}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        else:
            return [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful voice assistant.\n"
                        "Respond in the same language as the user's message.\n"
                        "- If the user speaks English, reply in English.\n"
                        "- If the user speaks Arabic, reply in **Egyptian Arabic (العامية المصرية)** "
                        "- Always use Egyptian colloquial expressions, not Modern Standard Arabic."
                        "using natural spoken slang.\n"
                        "Avoid Modern Standard Arabic (فصحى). Use 'عايز' instead of 'أريد', "
                        "'إزيك' instead of 'كيف حالك', etc.\n"
                        "Example:\n"
                        "User: 'عايز أعرف الفرق بين بايثون وسي بلس بلس'\n"
                        "Assistant: 'تمام، الفرق الأساسي إن بايثون لغة مفسرة وسهلة، أما سي بلس بلس لغة compiled وأسرع بكتير. تحب أشرحلك أكتر؟'\n"
                        "Keep responses concise and suitable for spoken conversation."
                    )
                }
            ]

    async def save_history(self, session_id: str, history: List[Dict[str, str]]):
        key = f"conversation:{session_id}"
        await self.redis.set(key, json.dumps(history))
        await self.redis.expire(key, 86400)

    async def delete_history(self, session_id: str):
        key = f"conversation:{session_id}"
        await self.redis.delete(key)