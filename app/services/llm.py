import asyncio
from groq import Groq
from app.config import settings

class LLMService:
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)

    async def generate_response(self, messages: list[dict]) -> str:
        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=settings.llm_model,
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content