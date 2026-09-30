# API request/response models + the format the LLM has to return
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class SkillRequirement(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    weight: float = Field(default=1.0, gt=0, le=5, description="How much this skill matters for the role")
    required_level: int = Field(default=3, ge=1, le=5, description="Level (1-5) a hire needs on day one")
    critical: bool = Field(default=False, description="A gap here blocks 'Suitable', whatever the total")
    keywords: list[str] = Field(default_factory=list, description="Only used by the mock evaluator")

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()


class RoleCreate(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=2000)
    skills: list[SkillRequirement] = Field(min_length=1, max_length=12)

    @field_validator("skills")
    @classmethod
    def unique_skill_names(cls, skills: list[SkillRequirement]) -> list[SkillRequirement]:
        names = [s.name.lower() for s in skills]
        if len(names) != len(set(names)):
            raise ValueError("Each skill can only be listed once")
        return skills


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    skills: list[SkillRequirement]


class InterviewCreate(BaseModel):
    role_id: int
    candidate_name: str = Field(min_length=1, max_length=120)
    candidate_email: EmailStr | None = None


class InterviewOut(BaseModel):
    id: str
    role_id: int
    role_title: str
    candidate_name: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None
    overall_score: float | None = None
    recommendation: str | None = None


class TranscriptTurn(BaseModel):
    role: Literal["candidate", "interviewer"]
    text: str = Field(max_length=10_000)
    at: str | None = None


class TranscriptIn(BaseModel):
    turns: list[TranscriptTurn] = Field(max_length=500)


class SessionConfig(BaseModel):
    token: str
    ws_url: str
    session: dict


# LLM output
class CriterionScore(BaseModel):
    score: int = Field(ge=1, le=5, description="1 = very weak, 3 = meets expectations, 5 = exceptional")
    evidence: str = Field(description="Short quote or paraphrase from the candidate that justifies the score")


class CriteriaScores(BaseModel):
    technical_knowledge: CriterionScore
    problem_solving: CriterionScore
    communication: CriterionScore
    behavioural: CriterionScore


class SkillEvidence(BaseModel):
    skill: str = Field(description="Must exactly match one of the skill names provided")
    level: int = Field(ge=0, le=5, description="0 = no evidence in the interview, 1-5 = demonstrated level")
    evidence: str = Field(default="", description="Short quote from the candidate, empty if level is 0")


class Evaluation(BaseModel):
    criteria: CriteriaScores
    skills: list[SkillEvidence]
    strengths: list[str] = Field(description="2-4 specific strengths")
    weaknesses: list[str] = Field(description="2-4 specific weaknesses, written for an HR reader")
    improvement_tips: list[str] = Field(description="2-4 constructive, actionable tips addressed to the candidate")
    summary: str = Field(description="Two or three neutral sentences summarising the interview")
