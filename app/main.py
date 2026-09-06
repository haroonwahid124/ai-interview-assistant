from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.voice.assemblyai_client import get_voice_agent_token

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/voice-token")
def voice_token():
    token = get_voice_agent_token()
    return {"token": token}