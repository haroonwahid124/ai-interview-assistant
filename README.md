# AI Interview Assistance


## Project Flow
Company/Role → AI Voice Interview → Answer Analysis → Candidate Scoring → 
Role-Fit Engine → HR/Candidate Report → Hiring Decision

## Architecture
See docs/architecture.md

## Getting Started
1. Clone the repo
2. cp infra/env/.env.example infra/env/.env
3. docker-compose -f infra/docker-compose.yml up
4. Backend: http://localhost:8080 | AI service: http://localhost:8000 | Frontend: http://localhost:3000

## Team
| Name | Role | Focus |
|---|---|---|
| ... | ... | Backend / AI / Frontend / Voice |

## Tech Stack
- Backend: Spring Boot
- AI/Analysis: Python (FastAPI)
- Frontend: React
- DB: PostgreSQL

## Contributing
- Branch naming: feature/<short-desc>, fix/<short-desc>
- PRs require 1 review before merge
- Conventional commits (feat:, fix:, docs:, refactor:)
