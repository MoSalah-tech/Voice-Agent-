import asyncio
from groq import Groq
from app.config import settings

class LLMService:
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)

    async def generate_response(self, messages: list[dict]) -> str:
        """Non‑streaming response (batch)."""
        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=settings.llm_model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
            stream=False
        )
        return response.choices[0].message.content

    async def stream_response(self, messages: list[dict]):
        """Stream tokens as an async generator."""
        stream = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=settings.llm_model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
            stream=True
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content