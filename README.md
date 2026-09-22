# AI Interview Assistance

Automates first-round interviews with AI voice screening. Scores candidates on technical,
problem-solving, communication and behavioural answers, then maps them against every open
role and gives HR a clear, explained recommendation. Candidates get useful feedback too.

Built for the **AssemblyAI Voice Agent Hackathon** (lablab.ai, Sep 1–30, 2026).

## Why this over other interview-AI projects
Most entries focus on candidate-side practice. This project is **HR-decision focused**: it
maps each candidate against multiple roles (Best fit / Suitable / Possible with training /
Not suitable) and outputs a structured hiring recommendation with its reasons, alongside
candidate-facing feedback.

**The AI judges, the code decides.** Claude scores each answer with quoted evidence. The
overall score, role fit and recommendation come from fixed, tested rules, so the same answers
always get the same result and HR can see exactly why.

## How it works
```
Company/Role → AI Voice Interview → Answer Analysis → Candidate Scoring
            → Role-Fit Engine → HR/Candidate Report → Hiring Decision (by a person)
```
Details: [`docs/project-flow.md`](docs/project-flow.md) and [`docs/architecture.md`](docs/architecture.md).

## Tech stack
| Layer | Choice |
|---|---|
| Voice agent (speech-to-text, turn-taking, voice) | AssemblyAI Voice Agent API |
| Transcript scoring | Claude (structured output via forced tool use) |
| API | Python, FastAPI, SQLAlchemy, Pydantic |
| UI | React + Vite |
| Database | SQLite locally, Postgres in production |
| Hosting | Vercel |

## Project structure
```
app/
  main.py                   HTTP routes
  schemas.py                request/response and LLM output shapes
  models.py, db.py          database tables and sessions
  seed.py                   four starter roles
  interview/questions.py    voice agent prompt built from the role
  interview/session.py      interview lifecycle
  voice/assemblyai_client.py  single-use voice tokens
  analysis/llm_client.py    Claude evaluator + offline mock
  analysis/scoring.py       overall score
  role_fit/engine.py        role-fit engine
  reports/generator.py      recommendation rules and report views
frontend/src/
  hooks/useVoiceInterview.js  mic, audio, WebSocket events
  pages/                    dashboard, role form, interview room, reports
tools/fake_voice_agent.py   offline stand-in for AssemblyAI
tests/                      35 tests
```

## Run locally

Requirements: Python 3.12+, Node 20+, Chrome or Edge.

```bash
# 1. Backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                 # then add your keys
uvicorn app.main:app --reload        # http://localhost:8000/api/health

# 2. Frontend (second terminal)
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

Open http://localhost:5173, create an interview link, and open it. Use headphones.

### Develop without spending credits
```bash
python tools/fake_voice_agent.py     # third terminal
```
In `.env` set `ASSEMBLYAI_WS_URL=ws://localhost:8765` and `LLM_PROVIDER=mock`, then restart
the API. The fake agent plays silence and treats every ~1.5 s of mic audio as a scripted
answer, so the whole flow runs offline. Mock scores are placeholders.

### Environment variables
| Variable | Purpose |
|---|---|
| `ASSEMBLYAI_API_KEY` | Server-side only; used to mint single-use browser tokens |
| `ASSEMBLYAI_WS_URL` | Voice agent WebSocket URL |
| `VOICE_AGENT_VOICE` | Interviewer voice |
| `LLM_PROVIDER` | `anthropic` for real scoring, `mock` for offline |
| `LLM_API_KEY`, `LLM_MODEL` | Claude API key and model |
| `DATABASE_URL` | SQLite or Postgres URL |
| `MAX_INTERVIEW_SECONDS` | Hard cap on one voice session |

## Tests
```bash
pytest
```
Covers the scoring maths, role-fit categories, recommendation rules, LLM output
clean-up, and the full API flow (with the mock evaluator, so no network calls).

## Deploy to Vercel
1. Create a free hosted Postgres database (for example Neon or Supabase) and copy its
   connection URL. Vercel functions have no persistent disk, so SQLite won't work there.
2. Import the GitHub repo into Vercel. It detects FastAPI from `app/main.py`.
3. Add the environment variables above in Project Settings, with `DATABASE_URL` set to
   the Postgres URL and `LLM_PROVIDER=anthropic`.
4. Deploy. `vercel.json` builds the frontend (`frontend/dist`), which FastAPI mounts and
   Vercel serves from its CDN, and gives the scoring request up to 60 seconds.

Check [Vercel's FastAPI docs](https://vercel.com/docs/frameworks/backend/fastapi) if the
build settings have changed.

## Run with Docker
```bash
cp .env.example .env    # add keys
docker compose up --build
```
Open http://localhost:8000. This runs the app with a Postgres container.

## Limitations
No login yet (HR pages are open to anyone with the URL), no rate limiting, tables created
on startup instead of migrations, and no data retention policy. See
[`docs/architecture.md`](docs/architecture.md#known-limitations-before-real-world-use).

## Team
| Name | Role | Focus |
|---|---|---|
| ... | ... | Voice pipeline / Scoring & role-fit / UI |

## Contributing
- Branch naming: `feature/<short-desc>`, `fix/<short-desc>`
- PRs require 1 review before merge
- Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`)

## Submission checklist (lablab.ai)
- [ ] Project title, short + long description
- [ ] Technology and category tags
- [ ] Cover image (PNG/JPG, 16:9)
- [ ] Demo video (MP4, under 5 min)
- [ ] Slide deck (PDF)
- [ ] Public GitHub repository (this repo)
- [ ] Live demo URL
- [ ] Submitted before Sep 30, 2026, 15:00 UTC

## Hackathon links
- Hackathon: https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon
