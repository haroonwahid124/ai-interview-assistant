import os
import requests
from dotenv import load_dotenv

load_dotenv()

ASSEMBLYAI_API_KEY = os.environ["ASSEMBLYAI_API_KEY"]


def get_voice_agent_token(expires_in_seconds: int = 300, max_session_duration_seconds: int = 8640) -> str:
    response = requests.get(
        "https://agents.assemblyai.com/v1/token",
        headers={"Authorization": f"Bearer {ASSEMBLYAI_API_KEY}"},
        params={
            "expires_in_seconds": expires_in_seconds,
            "max_session_duration_seconds": max_session_duration_seconds,
        },
    )
    response.raise_for_status()
    return response.json()["token"]