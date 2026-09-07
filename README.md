# 🎙️ Mo Salah Voice Agent

A full‑stack, real‑time conversational AI voice assistant. Users speak in English or Egyptian Arabic, and the agent replies naturally with speech, maintaining context across turns. Built with FastAPI, Next.js, WebSockets, Redis, and free LLM/STT/TTS APIs.

---

## ✨ Features

- **Real‑time voice interaction** – Streams audio chunks, auto‑detects silence (VAD), and responds without manual stop buttons.
- **Bilingual support** – English and Egyptian Arabic. The LLM is prompted to use colloquial Egyptian dialect when the user speaks Arabic.
- **Conversation memory** – Redis stores session history, so context persists across reconnections (using a client‑side session ID).
- **Interrupt handling** – If the user starts speaking while the assistant is talking, the backend cancels the previous response and listens anew.
- **Streaming output** – Text and audio chunks are streamed as they become available for a near‑real‑time feel.
- **Markdown rendering** – Assistant responses that contain tables, lists, or bold text are displayed beautifully in the frontend.
- **Custom TTS voices** – Uses Edge TTS by default (Egyptian Arabic: `ar‑EG‑SalmaNeural`, English: `en‑US‑AriaNeural`). Can be swapped with gTTS.
- **Dockerized** – Both backend and frontend are containerized for easy deployment.

---

## 🧱 Architecture


---

## 🛠️ Tech Stack

**Backend**
- Python 3.11+
- FastAPI
- Uvicorn
- Groq Python SDK (STT + LLM)
- Edge TTS (`edge-tts`) or gTTS
- Redis (`redis.asyncio`)

**Frontend**
- Next.js 14+ (App Router)
- React 18
- TypeScript
- Tailwind CSS (optional, custom CSS also provided)
- `react-markdown` + `remark-gfm` for Markdown rendering

**Infrastructure**
- Docker, Docker Compose
- Railway (backend deployment)
- Vercel (frontend deployment)


---

## 🚀 Getting Started

### Prerequisites

- **Groq API key** – [Get one free](https://console.groq.com)
- **Redis** – Local instance or Docker
- **Node.js 18+** (for frontend)
- **Python 3.11+** and **uv** (or pip) for backend

### Environment Variables

Create a `.env` file in the backend directory (or set in Docker Compose). Example:

```ini
GROQ_API_KEY=your_groq_api_key_here
STT_MODEL=whisper-large-v3
LLM_MODEL=openai/gpt-oss-120b      # or llama-3.3-70b-versatile
TTS_VOICE_ENGLISH=en-US-AriaNeural
TTS_VOICE_ARABIC=ar-EG-SalmaNeural
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
MAX_HISTORY_MESSAGES=10
AUDIO_FORMAT=webm
MAX_TOKENS=1000



```

## 🖥️ Local Development
### Using Docker Compose (recommended)
- Clone the repo.
- In the backend folder, copy .env.example to .env and fill in your Groq API key.
- Start backend + Redis:
```bash
 docker-compose up --build

```
- In the frontend folder, install dependencies and run:
```bash
npm install
npm run dev

```
- Open http://localhost:3000. The frontend will connect to ws://localhost:8001/ws/voice.



## 📡 WebSocket API
### Endpoint: ws://<host>:<port>/ws/voice?session_id=<uuid>

### Client → Server
 - Binary messages: Audio chunks (WebM/MP3 format). Sent continuously while recording.
 - Text messages: JSON control signals.
   -{"type": "end"} – indicates the user has stopped speaking; backend will process buffered audio.

 ### Server → Client
 - {"type": "user_text", "text": "..."} – final transcription of user input.
 - {"type": "assistant_start"} – signals the beginning of assistant response.
 - {"type": "assistant_text", "text": "..."} – partial assistant text (streamed, may include Markdown).
 - {"type": "assistant_end"} – assistant finished; audio queue complete.
 - {"type": "error", "detail": "..."} – error message.
 - "type": "cancelled"} – previous response cancelled due to user interruption.
 - Binary messages: MP3 audio chunks containing the assistant’s spoken response.



## 🧠 Conversation Memory

- Each client generates a UUID session_id and stores it in localStorage.
- The backend uses this ID to save/load conversation history from Redis.
- After every turn, the history is updated and saved with a TTL of 24 hours.
- History is trimmed to the last MAX_HISTORY_MESSAGES messages to avoid token overflow.


## 🎛️ Voice Activity Detection (VAD)

### The frontend uses the Web Audio API to measure microphone energy. When the RMS volume falls below a threshold for a configurable duration (default 600 ms), it automatically stops recording and sends the end signal.

Adjust SILENCE_THRESHOLD and SILENCE_DURATION in frontend/app/page.tsx for different microphones or environments.



## 🌍 Bilingual & Egyptian Arabic Support
- The system prompt instructs the LLM to respond in the same language as the user.
- For Arabic input, the prompt specifically asks for Egyptian colloquial Arabic (not Modern Standard Arabic).
- The TTS voice automatically switches between English (en-US-AriaNeural) and Arabic (ar-EG-SalmaNeural) based on Unicode detection.
- To change the Egyptian voice, set TTS_VOICE_ARABIC to another Edge TTS voice, e.g., ar-EG-ShakirNeural (male).




   

