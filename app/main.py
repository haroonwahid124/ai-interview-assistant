"""
HTTP layer. Each route validates input, calls the logic in app/interview,
and turns known errors into sensible HTTP status codes.

Note on auth: there is none. Anyone with the URL can see the HR pages.
That's acceptable for a hackathon demo but must be added before real use
(see docs/architecture.md).
"""
from contextlib import asynccontextmanager
from datetime import timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.analysis.llm_client import EvaluationError
from app.config import settings
from app.db import Base, SessionLocal, engine, get_db
from app.interview import session as interviews
from app.models import Interview, InterviewStatus, Role
from app.reports.generator import candidate_view, hr_view
from app.schemas import InterviewCreate, InterviewOut, RoleCreate, RoleOut, SessionConfig, TranscriptIn
from app.seed import seed_roles
from app.voice.assemblyai_client import VoiceProviderError


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Creates tables on startup. Fine for a demo; a real project would use Alembic migrations.
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_roles(db)
    yield


app = FastAPI(title="AI Interview Assistant", lifespan=lifespan)

# No CORS middleware: the frontend is served from the same origin as the API
# (Vite proxies /api in development). Leaving out top-level middleware also lets
# Vercel serve the built frontend straight from its CDN.


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_interview_or_404(db: Session, interview_id: str) -> Interview:
    interview = db.get(Interview, interview_id)
    if interview is None:
        raise HTTPException(404, "Interview not found.")
    return interview


def as_utc(value):
    """SQLite drops timezone info; everything is stored in UTC, so put it back."""
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def to_interview_out(interview: Interview) -> InterviewOut:
    report = interview.report or {}
    return InterviewOut(
        id=interview.id,
        role_id=interview.role_id,
        role_title=interview.role.title,
        candidate_name=interview.candidate_name,
        status=interview.status,
        created_at=as_utc(interview.created_at),
        completed_at=as_utc(interview.completed_at),
        overall_score=report.get("overall_score"),
        recommendation=(report.get("recommendation") or {}).get("label"),
    )


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------


@app.get("/api/health")
def health():
    return {"status": "ok", "llm_provider": settings.llm_provider}


@app.get("/api/roles", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db)):
    return db.query(Role).order_by(Role.title).all()


@app.post("/api/roles", response_model=RoleOut, status_code=201)
def create_role(data: RoleCreate, db: Session = Depends(get_db)):
    role = Role(title=data.title.strip(), description=data.description.strip(),
                skills=[s.model_dump() for s in data.skills])
    db.add(role)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, f"A role called '{data.title}' already exists.")
    db.refresh(role)
    return role


# ---------------------------------------------------------------------------
# Interviews
# ---------------------------------------------------------------------------


@app.get("/api/interviews", response_model=list[InterviewOut])
def list_interviews(db: Session = Depends(get_db)):
    rows = db.query(Interview).order_by(Interview.created_at.desc()).all()
    return [to_interview_out(i) for i in rows]


@app.post("/api/interviews", response_model=InterviewOut, status_code=201)
def create_interview(data: InterviewCreate, db: Session = Depends(get_db)):
    try:
        return to_interview_out(interviews.create_interview(db, data))
    except interviews.InterviewError as exc:
        raise HTTPException(404, str(exc))


@app.get("/api/interviews/{interview_id}", response_model=InterviewOut)
def get_interview(interview_id: str, db: Session = Depends(get_db)):
    return to_interview_out(get_interview_or_404(db, interview_id))


@app.post("/api/interviews/{interview_id}/session", response_model=SessionConfig)
def start_session(interview_id: str, db: Session = Depends(get_db)):
    """POST, not GET: every call mints a new single-use token."""
    interview = get_interview_or_404(db, interview_id)
    try:
        return interviews.start_voice_session(interview)
    except interviews.InterviewError as exc:
        raise HTTPException(409, str(exc))
    except VoiceProviderError as exc:
        raise HTTPException(503, f"Voice service unavailable: {exc}")


@app.post("/api/interviews/{interview_id}/transcript", response_model=InterviewOut)
def submit_transcript(interview_id: str, data: TranscriptIn, db: Session = Depends(get_db)):
    interview = get_interview_or_404(db, interview_id)
    try:
        interviews.save_transcript(db, interview, data.turns)
        interviews.evaluate_interview(db, interview)
    except interviews.InterviewError as exc:
        raise HTTPException(422, str(exc))
    except EvaluationError as exc:
        # The transcript is saved, so HR can retry scoring later.
        raise HTTPException(502, f"Your answers were saved, but scoring failed: {exc}")
    return to_interview_out(interview)


@app.post("/api/interviews/{interview_id}/evaluate", response_model=InterviewOut)
def retry_evaluation(interview_id: str, db: Session = Depends(get_db)):
    interview = get_interview_or_404(db, interview_id)
    if interview.status == InterviewStatus.COMPLETED:
        return to_interview_out(interview)
    try:
        interviews.evaluate_interview(db, interview)
    except interviews.InterviewError as exc:
        raise HTTPException(422, str(exc))
    except EvaluationError as exc:
        raise HTTPException(502, f"Scoring failed again: {exc}")
    return to_interview_out(interview)


@app.get("/api/interviews/{interview_id}/report/hr")
def hr_report(interview_id: str, db: Session = Depends(get_db)):
    interview = get_interview_or_404(db, interview_id)
    if interview.report is None:
        raise HTTPException(404, interview.error or "The report isn't ready yet.")
    return hr_view(interview.report, interview.transcript)


@app.get("/api/interviews/{interview_id}/report/candidate")
def candidate_report(interview_id: str, db: Session = Depends(get_db)):
    interview = get_interview_or_404(db, interview_id)
    if interview.report is None:
        raise HTTPException(404, "Your results aren't ready yet.")
    return candidate_view(interview.report)


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------
# `npm run build` writes the React app to frontend/dist. Mounted last so API
# routes always win. On Vercel the files are promoted to the CDN at build time.

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if (FRONTEND_DIST / "index.html").is_file():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
