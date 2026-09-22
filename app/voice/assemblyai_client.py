"""
AssemblyAI Voice Agent tokens.

The browser can't be given our real API key, and browsers can't set an
Authorization header on a WebSocket. So the server asks AssemblyAI for a
short-lived, single-use token and hands only that to the browser, which
passes it as ?token=... when it opens the socket.
"""
import requests

from app.config import settings

TOKEN_URL = "https://agents.assemblyai.com/v1/token"


class VoiceProviderError(RuntimeError):
    pass


def get_voice_agent_token(expires_in_seconds: int = 120, max_session_duration_seconds: int | None = None) -> str:
    """
    expires_in_seconds: how long the browser has to *open* the socket.
    max_session_duration_seconds: hard cap on the whole conversation.
    """
    if settings.assemblyai_ws_url.startswith(("ws://localhost", "ws://127.0.0.1")):
        return "local-dev-token"  # tools/fake_voice_agent.py doesn't check tokens

    if not settings.assemblyai_api_key:
        raise VoiceProviderError("ASSEMBLYAI_API_KEY is not set on the server.")

    response = requests.get(
        TOKEN_URL,
        headers={"Authorization": f"Bearer {settings.assemblyai_api_key}"},
        params={
            "expires_in_seconds": expires_in_seconds,
            "max_session_duration_seconds": max_session_duration_seconds or settings.max_interview_seconds,
        },
        timeout=10,
    )
    if response.status_code != 200:
        raise VoiceProviderError(f"AssemblyAI token request failed ({response.status_code}): {response.text[:200]}")
    return response.json()["token"]
