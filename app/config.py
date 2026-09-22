"""
All configuration comes from environment variables (or a local .env file).

Keeping settings in one place means the rest of the code never calls
os.getenv directly, which makes it easy to see what the app depends on.
"""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # AssemblyAI Voice Agent (speech-to-text + agent LLM + text-to-speech in one socket)
    assemblyai_api_key: str = os.getenv("ASSEMBLYAI_API_KEY", "")
    assemblyai_ws_url: str = os.getenv("ASSEMBLYAI_WS_URL", "wss://agents.assemblyai.com/v1/ws")
    voice: str = os.getenv("VOICE_AGENT_VOICE", "michael")

    # The LLM that scores the finished transcript.
    # "mock" needs no API key and is used for tests and offline development.
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "claude-sonnet-5")

    # SQLite locally; set a Postgres URL in production (Vercel functions have no persistent disk).
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./interview.db")

    # Hard cap on a single interview, enforced by the token AssemblyAI issues.
    max_interview_seconds: int = int(os.getenv("MAX_INTERVIEW_SECONDS", "1500"))


settings = Settings()
