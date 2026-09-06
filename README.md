# AI Interview Assistance

Automates first-round interviews with AI voice screening. Scores candidates on technical, behavioural, and communication skills, then outputs role-fit analysis and hiring recommendations — faster, fairer screening for HR and clearer feedback for candidates.

Built for the **AssemblyAI – Voice Agent Hackathon** (lablab.ai, Sep 1–30, 2026).

## Why this over other interview-AI projects
Most entries in this hackathon (e.g. MockMate, EchoExaminer, Interview Lab) focus on candidate-side practice/coaching. This project is **HR-decision focused**: it doesn't just score the candidate, it maps them against multiple roles (Best Fit / Suitable / Possible with Training / Not Suitable) and outputs a structured hiring recommendation for the employer, alongside candidate-facing feedback.

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
| Hosting (demo) | Vercel (must be Streamlit/Replit/Vercel per hackathon rules) |

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

## Submission Checklist (lablab.ai requirements)
- [ ] Project title, short + long description
- [ ] Technology and category tags
- [ ] Cover image — PNG/JPG, 16:9
- [ ] Demo video — MP4, under 5 min
- [ ] Slide deck — PDF
- [ ] Public GitHub repository (this repo)
- [ ] Live demo URL (Vercel/Replit/Streamlit)
- [ ] Submitted before Sep 30, 2026, 15:00 UTC

## Hackathon Links
- Hackathon: https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon
- Prize pool: $10,000 ($5k cash + $5k AssemblyAI credits)
