# fake AssemblyAI voice agent for testing without credits.
# plays silence and sends scripted answers (every ~1.5s of mic audio = 1 answer)
# run: python tools/fake_voice_agent.py  and set ASSEMBLYAI_WS_URL=ws://localhost:8765
import asyncio
import base64
import json

import websockets

HOST, PORT = "localhost", 8765
CHUNKS_PER_ANSWER = 30  # 30 x 50 ms = 1.5 s of mic audio

QUESTIONS = [
    "Tell me about an API you have built.",
    "How would you approach a slow endpoint?",
    "Tell me about a time you disagreed with a teammate.",
]
ANSWERS = [
    "I built a REST API in Python with FastAPI. It had JSON endpoints backed by a Postgres database and I wrote the SQL queries.",
    "First I would measure, because guessing wastes time. Then I would add an index or a cache, so repeated queries are cheap.",
    "My team disagreed about testing. We listened to each other, agreed on unit tests in CI, and I learned a lot from the feedback.",
]
SILENCE = base64.b64encode(bytes(2400 * 2)).decode()  # 50 ms of 24 kHz PCM16 silence x 2


async def send(ws, **event):
    await ws.send(json.dumps(event))


async def say(ws, text: str):
    await send(ws, type="reply.started")
    for _ in range(4):
        await send(ws, type="reply.audio", data=SILENCE)
        await asyncio.sleep(0.02)
    await send(ws, type="transcript.agent", text=text)


async def handle(ws):
    config = json.loads(await ws.recv())
    assert config["type"] == "session.update", config
    greeting = config["session"].get("greeting", "Hello!")
    await send(ws, type="session.ready", session_id="fake-session")
    await say(ws, greeting)
    await send(ws, type="reply.done")

    chunks = 0
    answered = 0
    waiting_for_tool_result = False

    async for raw in ws:
        event = json.loads(raw)
        kind = event["type"]

        if kind == "input.audio" and not waiting_for_tool_result and answered <= len(ANSWERS):
            chunks += 1
            if chunks < CHUNKS_PER_ANSWER:
                continue
            chunks = 0
            await send(ws, type="input.speech.started")
            await send(ws, type="input.speech.stopped")
            if answered == 0:
                await send(ws, type="transcript.user", text="Yes, I'm ready.")
            else:
                await send(ws, type="transcript.user", text=ANSWERS[answered - 1])

            if answered < len(QUESTIONS):
                await say(ws, QUESTIONS[answered])
                await send(ws, type="reply.done")
            else:
                await say(ws, "Thanks, that's everything from me.")
                await send(ws, type="tool.call", call_id="call_1", name="end_interview",
                           arguments={"reason": "completed"})
                await send(ws, type="reply.done")
                waiting_for_tool_result = True
            answered += 1

        elif kind == "tool.result":
            print("tool.result received:", event)
            await say(ws, "Your results will be ready shortly. Goodbye!")
            await send(ws, type="reply.done")

        elif kind == "session.end":
            await send(ws, type="session.ended", session_duration_seconds=12.3,
                       audio_duration_seconds=10.0, timestamp=0)
            await ws.close(1000)
            print("session ended cleanly")
            return


async def main():
    async with websockets.serve(handle, HOST, PORT):
        print(f"Fake voice agent listening on ws://{HOST}:{PORT}")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
