"""
Interview lifecycle: create -> start voice session -> save transcript -> evaluate.

These functions hold the business logic; main.py only translates HTTP
requests into calls to them. That split keeps the routes thin and lets
tests call the logic directly.
"""
from sqlalchemy.orm import Session

from app.analysis.llm_client import EvaluationError, get_evaluator
from app.config import settings
from app.interview.questions import END_INTERVIEW_TOOL, build_greeting, build_system_prompt
from app.models import Interview, InterviewStatus, Role, utcnow
from app.reports.generator import build_report
from app.schemas import InterviewCreate, SessionConfig, TranscriptTurn
from app.voice.assemblyai_client import get_voice_agent_token


class InterviewError(Exception):
    """Raised for problems the caller should show to the user (bad state, missing data)."""


def create_interview(db: Session, data: InterviewCreate) -> Interview:
    role = db.get(Role, data.role_id)
    if role is None:
        raise InterviewError("That role doesn't exist.")
    interview = Interview(
        role_id=role.id,
        candidate_name=data.candidate_name.strip(),
        candidate_email=(data.candidate_email or "").strip(),
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


def start_voice_session(interview: Interview) -> SessionConfig:
    if interview.status == InterviewStatus.COMPLETED:
        raise InterviewError("This interview has already been completed.")

    session = {
        "system_prompt": build_system_prompt(interview.role, interview.candidate_name),
        "greeting": build_greeting(interview.role, interview.candidate_name),
        "tools": [END_INTERVIEW_TOOL],
        "output": {"voice": settings.voice},
    }
    return SessionConfig(
        token=get_voice_agent_token(),
        ws_url=settings.assemblyai_ws_url,
        session=session,
    )


def save_transcript(db: Session, interview: Interview, turns: list[TranscriptTurn]) -> Interview:
    if interview.status == InterviewStatus.COMPLETED:
        raise InterviewError("This interview has already been completed.")

    cleaned = [t.model_dump() for t in turns if t.text.strip()]
    if not any(t["role"] == "candidate" for t in cleaned):
        raise InterviewError("No candidate answers were recorded. Check the microphone and try again.")

    interview.transcript = cleaned
    db.commit()
    return interview


def evaluate_interview(db: Session, interview: Interview) -> Interview:
    """Score a saved transcript. Safe to call again if a previous attempt failed."""
    if not interview.transcript:
        raise InterviewError("There is no transcript to evaluate yet.")

    all_roles = db.query(Role).order_by(Role.id).all()
    try:
        evaluation = get_evaluator().evaluate(interview.role, all_roles, interview.transcript)
    except EvaluationError as exc:
        interview.status = InterviewStatus.FAILED
        interview.error = str(exc)
        db.commit()
        raise

    interview.evaluation = evaluation.model_dump()
    interview.report = build_report(interview, all_roles, evaluation)
    interview.status = InterviewStatus.COMPLETED
    interview.error = ""
    interview.completed_at = utcnow()
    db.commit()
    return interview
