from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    groq_api_key: str
    llm_model: str = "openai/gpt-oss-120b"
    stt_model: str = "whisper-large-v3"
    tts_voice: str = "en-US-AriaNeural"
    log_level: str = "INFO"
    max_history_messages: int = 10

    # Redis settings
    redis_url: str = "redis://localhost:6379/0"
    audio_format: str = "webm"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",extra="ignore")



settings = Settings()
