# skills, transcript and report are JSON columns to keep it simple.
# reports are snapshots so editing a role later doesn't change old reports.
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    # [{"name", "weight", "required_level", "critical", "keywords"}]
    skills: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    interviews: Mapped[list["Interview"]] = relationship(back_populates="role")


class InterviewStatus:
    CREATED = "created"
    COMPLETED = "completed"
    FAILED = "failed"  # scoring failed, can retry


class Interview(Base):
    __tablename__ = "interviews"

    # uuid so interview links can't be guessed
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    candidate_name: Mapped[str] = mapped_column(String(120))
    candidate_email: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(20), default=InterviewStatus.CREATED)

    transcript: Mapped[list] = mapped_column(JSON, default=list)  # [{"role", "text", "at"}]
    evaluation: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # raw LLM output
    report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    role: Mapped[Role] = relationship(back_populates="interviews")
