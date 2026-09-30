"""API routes."""
from contextlib import asynccontextmanager
from datetime import timezone
from pathlib import Path

import time
from collections import defaultdict

from fastapi import Depends, FastAPI, Header, HTTPException, Request
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
    # TODO: use alembic migrations instead
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_roles(db)
    yield


app = FastAPI(title="AI Interview Assistant", lifespan=lifespan)
# no CORS needed, frontend is on the same origin (vite proxies /api in dev)


def require_hr_key(x_hr_key: str = Header(default="")) -> None:
    # HR routes only. skipped if HR_API_KEY is empty
    if settings.hr_api_key and x_hr_key != settings.hr_api_key:
        raise HTTPException(401, "Missing or invalid X-HR-Key header.")


# simple per-IP rate limit, every session costs AssemblyAI credit
_session_calls: dict[str, list[float]] = defaultdict(list)
SESSION_RATE_LIMIT = 5
SESSION_RATE_WINDOW = 60  # seconds


def enforce_session_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    recent = [t for t in _session_calls[ip] if now - t < SESSION_RATE_WINDOW]
    if len(recent) >= SESSION_RATE_LIMIT:
        raise HTTPException(429, "Too many interview sessions started. Please wait a minute and try again.")
    recent.append(now)
    _session_calls[ip] = recent


def get_interview_or_404(db: Session, interview_id: str) -> Interview:
    interview = db.get(Interview, interview_id)
    if interview is None:
        raise HTTPException(404, "Interview not found.")
    return interview


def as_utc(value):
    # sqlite loses the timezone, everything is stored as UTC
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


@app.get("/api/health")
def health():
    return {"status": "ok", "llm_provider": settings.llm_provider}


@app.get("/api/roles", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db)):
    return db.query(Role).order_by(Role.title).all()


@app.post("/api/roles", response_model=RoleOut, status_code=201, dependencies=[Depends(require_hr_key)])
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


@app.get("/api/interviews", response_model=list[InterviewOut], dependencies=[Depends(require_hr_key)])
def list_interviews(db: Session = Depends(get_db)):
    rows = db.query(Interview).order_by(Interview.created_at.desc()).all()
    return [to_interview_out(i) for i in rows]


@app.post("/api/interviews", response_model=InterviewOut, status_code=201, dependencies=[Depends(require_hr_key)])
def create_interview(data: InterviewCreate, db: Session = Depends(get_db)):
    try:
        return to_interview_out(interviews.create_interview(db, data))
    except interviews.InterviewError as exc:
        raise HTTPException(404, str(exc))


@app.get("/api/interviews/{interview_id}", response_model=InterviewOut)
def get_interview(interview_id: str, db: Session = Depends(get_db)):
    return to_interview_out(get_interview_or_404(db, interview_id))


@app.post(
    "/api/interviews/{interview_id}/session",
    response_model=SessionConfig,
    dependencies=[Depends(enforce_session_rate_limit)],
)
def start_session(interview_id: str, db: Session = Depends(get_db)):
    # POST because each call creates a new token
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
        # transcript is already saved so scoring can be retried
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


@app.get("/api/interviews/{interview_id}/report/hr", dependencies=[Depends(require_hr_key)])
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


# serve the built react app (npm run build). mounted last so /api routes come first
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if (FRONTEND_DIST / "index.html").is_file():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
