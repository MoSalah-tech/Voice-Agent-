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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

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

    try:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                logger.info("Client disconnected")
                break

            if message.get("bytes") is None:
                await websocket.send_json({"type": "error", "detail": "Expected binary audio data"})
                continue

            audio_bytes = message["bytes"]
            # 1. STT
            try:
                transcript = await stt_service.transcribe(audio_bytes)
                logger.info(f"User said: {transcript}")
            except Exception as e:
                await websocket.send_json({"type": "error", "detail": f"STT failed: {str(e)}"})
                continue

            # 2. Update history
            conversation_history.append({"role": "user", "content": transcript})
            if len(conversation_history) > settings.max_history_messages + 1:
                conversation_history = [conversation_history[0]] + conversation_history[-settings.max_history_messages:]

            # 3. LLM
            try:
                assistant_text = await llm_service.generate_response(conversation_history)
                logger.info(f"Assistant: {assistant_text}")
            except Exception as e:
                await websocket.send_json({"type": "error", "detail": f"LLM failed: {str(e)}"})
                continue

            conversation_history.append({"role": "assistant", "content": assistant_text})

            # 4. Save history
            try:
                await memory_service.save_history(session_id, conversation_history)
            except Exception as e:
                await websocket.send_json({"type": "error", "detail": f"Memory save failed: {str(e)}"})
                continue

            # 5. TTS
            try:
                audio_response = await tts_service.synthesize(assistant_text)
            except Exception as e:
                await websocket.send_json({"type": "error", "detail": f"TTS failed: {str(e)}"})
                continue

            # 6. Send back
            await websocket.send_json({
                "type": "result",
                "user_text": transcript,
                "assistant_text": assistant_text
            })
            await websocket.send_bytes(audio_response)

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        await websocket.close(code=1011)