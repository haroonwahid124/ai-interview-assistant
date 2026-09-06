# AI Interview Assistance

Automates first-round interviews with AI voice screening. Scores candidates on technical, behavioural, and communication skills, then outputs role-fit analysis and hiring recommendations — faster, fairer screening for HR and clearer feedback for candidates.

Built for the **AssemblyAI – Voice Agent Hackathon** (lablab.ai, Sep 1–30, 2026).

## Project Flow
Company/Role → AI Voice Interview → Answer Analysis → Candidate Scoring →
Role-Fit Engine → HR/Candidate Report → Hiring Decision

## Architecture
See `docs/architecture.md`

## Tech Stack

| Layer | Choice |
|---|---|
| Voice agent (STT + turn-taking) | **AssemblyAI** (Universal-Streaming / Voice Agent API) — required by hackathon rules |
| Text-to-Speech | ElevenLabs (fallback: browser Web Speech API) |
| LLM | Claude / GPT-4o (structured JSON output for scoring) |
| App | Single Python (FastAPI) service — interview session, scoring, role-fit engine, and API in one app |
| UI | React + Vite |
| Database | PostgreSQL |
| Hosting (demo) | Railway/Render (app + DB), Vercel (UI) |

Kept to one app rather than split services — faster to build and demo within a hackathon timeline.

## Getting Started
1. Clone the repo
2. `cp .env.example .env` and fill in API keys (AssemblyAI, LLM provider, ElevenLabs)
3. `docker-compose up`
4. App: http://localhost:8000 | UI: http://localhost:5173

## Team
| Name | Role | Focus |
|---|---|---|
| ... | ... | Voice pipeline / Scoring & role-fit / UI |

## Contributing
- Branch naming: `feature/<short-desc>`, `fix/<short-desc>`
- PRs require 1 review before merge
- Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`)

## Hackathon Links
- Hackathon: https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon
- Prize pool: $10,000 ($5k cash + $5k AssemblyAI credits)
