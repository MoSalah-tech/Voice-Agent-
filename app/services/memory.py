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
            return [{"role": "system", "content": "You are a helpful voice assistant. Keep responses concise and natural."}]

    async def save_history(self, session_id: str, history: List[Dict[str, str]]):
        key = f"conversation:{session_id}"
        await self.redis.set(key, json.dumps(history))
        await self.redis.expire(key, 86400)  # 24 hours TTL

    async def delete_history(self, session_id: str):
        key = f"conversation:{session_id}"
        await self.redis.delete(key)