"""Settings, read from env vars / .env"""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # AssemblyAI voice agent
    assemblyai_api_key: str = os.getenv("ASSEMBLYAI_API_KEY", "")
    assemblyai_ws_url: str = os.getenv("ASSEMBLYAI_WS_URL", "wss://agents.assemblyai.com/v1/ws")
    voice: str = os.getenv("VOICE_AGENT_VOICE", "michael")

    # scoring LLM, "mock" works without a key
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "claude-sonnet-5-5")

    # sqlite locally, postgres on vercel
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./interview.db")

    max_interview_seconds: int = int(os.getenv("MAX_INTERVIEW_SECONDS", "1500"))

    # X-HR-Key header for HR routes, leave empty to turn off
    hr_api_key: str = os.getenv("HR_API_KEY", "")


settings = Settings()
