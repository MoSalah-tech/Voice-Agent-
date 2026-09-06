import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services.stt import STTService
from app.services.llm import LLMService
from app.services.tts import TTSService
from app.services.memory import MemoryService

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
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
async def voice_agent_websocket(
    websocket: WebSocket,
    session_id: str = Query(default=None)
):
    await websocket.accept()
    logger.info(f"Client connected, session_id={session_id}")

    if not session_id:
        await websocket.close(code=1008, reason="session_id query parameter required")
        return

    # Load existing conversation history from Redis
    try:
        conversation_history = await memory_service.get_history(session_id)
        logger.info(f"Loaded history for session {session_id}, length={len(conversation_history)}")
    except Exception as e:
        logger.error(f"Failed to load history: {e}")
        await websocket.close(code=1011)
        return

    # Buffer to accumulate audio chunks for the current utterance
    audio_buffer = bytearray()

    try:
        while True:
            message = await websocket.receive()

            if message["type"] == "websocket.disconnect":
                logger.info("Client disconnected")
                break

            # Binary message = audio chunk, append to buffer
            if message.get("bytes") is not None:
                audio_buffer.extend(message["bytes"])
                logger.debug(f"Received {len(message['bytes'])} bytes, buffer size now {len(audio_buffer)}")
                continue

            # Text message = control signal (currently only "end")
            if message.get("text") is not None:
                try:
                    data = json.loads(message["text"])
                except json.JSONDecodeError:
                    await websocket.send_json({"type": "error", "detail": "Invalid JSON control message"})
                    continue

                if data.get("type") != "end":
                    await websocket.send_json({"type": "error", "detail": "Unknown control message"})
                    continue

                # End of utterance: process the buffered audio
                if len(audio_buffer) == 0:
                    await websocket.send_json({"type": "error", "detail": "No audio received"})
                    continue

                audio_bytes = bytes(audio_buffer)
                audio_buffer.clear()

                # 1. Transcribe
                try:
                    transcript = await stt_service.transcribe(audio_bytes,settings.audio_format)
                    logger.info(f"User said: {transcript}")
                except Exception as e:
                    logger.error(f"STT error: {e}")
                    await websocket.send_json({"type": "error", "detail": f"Speech recognition failed: {str(e)}"})
                    continue

                # 2. Append user message to history
                conversation_history.append({"role": "user", "content": transcript})

                # Trim history to avoid token overflow
                if len(conversation_history) > settings.max_history_messages + 1:
                    conversation_history = [conversation_history[0]] + conversation_history[-settings.max_history_messages:]

                # 3. Generate LLM response
                try:
                    assistant_text = await llm_service.generate_response(conversation_history)
                    logger.info(f"Assistant: {assistant_text}")
                except Exception as e:
                    logger.error(f"LLM error: {e}")
                    await websocket.send_json({"type": "error", "detail": f"Language model failed: {str(e)}"})
                    continue

                # 4. Append assistant reply to history
                conversation_history.append({"role": "assistant", "content": assistant_text})

                # 5. Save updated history to Redis
                try:
                    await memory_service.save_history(session_id, conversation_history)
                except Exception as e:
                    logger.error(f"Failed to save history: {e}")
                    await websocket.send_json({"type": "error", "detail": f"Memory save failed: {str(e)}"})
                    continue

                # 6. Synthesize speech
                try:
                    audio_response = await tts_service.synthesize(assistant_text)
                    logger.debug(f"Generated {len(audio_response)} bytes of TTS audio")
                except Exception as e:
                    logger.error(f"TTS error: {e}")
                    await websocket.send_json({"type": "error", "detail": f"Speech synthesis failed: {str(e)}"})
                    continue

                # 7. Send results
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