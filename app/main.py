import json
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services.stt import STTService
from app.services.llm import LLMService
from app.services.tts import TTSService
from app.services.memory import MemoryService

logging.basicConfig(level=settings.log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

stt_service = STTService()
llm_service = LLMService()
tts_service = TTSService()
memory_service = MemoryService()

app = FastAPI(title="Voice Agent Backend", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}

async def process_utterance(websocket, session_id, conversation_history, audio_bytes):
    """Handle a complete utterance: STT → LLM → TTS → send result."""
    try:
        # 1. Transcribe
        transcript = await stt_service.transcribe(audio_bytes, settings.audio_format)
        logger.info(f"User said: {transcript}")

        # 2. Update history with user message
        conversation_history.append({"role": "user", "content": transcript})
        if len(conversation_history) > settings.max_history_messages + 1:
            conversation_history = [conversation_history[0]] + conversation_history[-settings.max_history_messages:]

        # 3. Generate LLM response
        assistant_text = await llm_service.generate_response(conversation_history)
        logger.info(f"Assistant: {assistant_text}")

        # 4. Save assistant reply
        conversation_history.append({"role": "assistant", "content": assistant_text})
        await memory_service.save_history(session_id, conversation_history)

        # 5. Synthesize speech
        audio_response = await tts_service.synthesize(assistant_text)

        # 6. Send results
        await websocket.send_json({
            "type": "result",
            "user_text": transcript,
            "assistant_text": assistant_text
        })
        await websocket.send_bytes(audio_response)

    except asyncio.CancelledError:
        logger.info("Processing task cancelled")
        # Re-raise to properly handle cancellation
        raise
    except Exception as e:
        logger.error(f"Processing error: {e}")
        await websocket.send_json({"type": "error", "detail": str(e)})


@app.websocket("/ws/voice")
async def voice_agent_websocket(websocket: WebSocket, session_id: str = Query(default=None)):
    await websocket.accept()
    logger.info(f"Client connected, session_id={session_id}")

    if not session_id:
        await websocket.close(code=1008, reason="session_id query parameter required")
        return

    try:
        conversation_history = await memory_service.get_history(session_id)
    except Exception as e:
        logger.error(f"Failed to load history: {e}")
        await websocket.close(code=1011)
        return

    audio_buffer = bytearray()
    current_task = None

    try:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break

            # If binary audio arrives while a task is running → user is interrupting
            if message.get("bytes") is not None:
                if current_task and not current_task.done():
                    logger.info("Interrupting current response")
                    current_task.cancel()
                    await websocket.send_json({"type": "cancelled"})
                audio_buffer.extend(message["bytes"])
                continue

            # Text control message
            if message.get("text") is not None:
                data = json.loads(message["text"])
                if data.get("type") != "end":
                    continue

                if len(audio_buffer) == 0:
                    await websocket.send_json({"type": "error", "detail": "No audio received"})
                    continue

                audio_bytes = bytes(audio_buffer)
                audio_buffer.clear()

                # Cancel any previous unfinished task
                if current_task and not current_task.done():
                    current_task.cancel()

                # Launch new processing task
                current_task = asyncio.create_task(
                    process_utterance(websocket, session_id, conversation_history, audio_bytes)
                )

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
    finally:
        if current_task and not current_task.done():
            current_task.cancel()
        await websocket.close()