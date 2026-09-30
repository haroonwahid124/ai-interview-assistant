# builds the report + HR/candidate views.
# recommendation uses fixed rules (not the LLM) so it's consistent
from datetime import datetime, timezone

from app.analysis.scoring import CRITERIA_LABELS, CRITERIA_WEIGHTS, criterion_percent, overall_score
from app.role_fit.engine import BEST_FIT, CATEGORY_LABELS, SUITABLE, TRAINING, RoleFit, rank_roles
from app.schemas import Evaluation

MIN_CANDIDATE_TURNS = 3

RECOMMENDATION_LABELS = {
    "strongly_recommend": "Strongly recommend",
    "consider": "Consider",
    "further_interview": "Further interview",
    "not_recommended": "Not recommended",
}

ADVISORY_NOTICE = (
    "This is an automated first-round assessment to support, not replace, a hiring decision. "
    "A member of the hiring team should review the transcript before acting on it."
)


def recommend(overall: float, applied_fit: RoleFit, candidate_turns: int) -> tuple[str, list[str]]:
    reasons: list[str] = []

    if candidate_turns < MIN_CANDIDATE_TURNS:
        reasons.append(
            f"Only {candidate_turns} answer(s) were recorded, which is not enough evidence for a reliable score."
        )
        return "further_interview", reasons

    good_fit = applied_fit.category in (BEST_FIT, SUITABLE)
    reasons.append(f"Overall score {overall:.0f}%.")
    reasons.append(
        f"Fit for the applied role: {applied_fit.fit_score:.0f}% ({CATEGORY_LABELS[applied_fit.category].lower()})."
    )
    for gap in applied_fit.critical_gaps:
        reasons.append(
            f"Critical gap in {gap.skill}: showed level {gap.candidate_level}, role needs {gap.required_level}."
        )

    if overall >= 80 and good_fit:
        return "strongly_recommend", reasons
    if overall >= 65 and good_fit:
        return "consider", reasons
    if overall >= 50 or applied_fit.category == TRAINING:
        return "further_interview", reasons
    return "not_recommended", reasons


def build_report(interview, all_roles, evaluation: Evaluation) -> dict:
    criteria_scores = {name: getattr(evaluation.criteria, name).score for name in CRITERIA_WEIGHTS}
    overall = overall_score(criteria_scores)

    levels = {s.skill.lower(): s.level for s in evaluation.skills}
    role_dicts = [{"id": r.id, "title": r.title, "skills": r.skills} for r in all_roles]
    fits = rank_roles(role_dicts, levels)
    applied_fit = next(f for f in fits if f.role_id == interview.role_id)

    candidate_turns = sum(1 for t in interview.transcript if t["role"] == "candidate")
    code, reasons = recommend(overall, applied_fit, candidate_turns)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_name": interview.candidate_name,
        "applied_role_id": interview.role_id,
        "applied_role": interview.role.title,
        "overall_score": overall,
        "criteria": [
            {
                "key": name,
                "label": CRITERIA_LABELS[name],
                "score": criteria_scores[name],
                "percent": criterion_percent(criteria_scores[name]),
                "weight": weight,
                "evidence": getattr(evaluation.criteria, name).evidence,
            }
            for name, weight in CRITERIA_WEIGHTS.items()
        ],
        "skills": [s.model_dump() for s in evaluation.skills],
        "role_fit": [f.to_dict() for f in fits],
        "strengths": evaluation.strengths,
        "weaknesses": evaluation.weaknesses,
        "improvement_tips": evaluation.improvement_tips,
        "summary": evaluation.summary,
        "recommendation": {
            "code": code,
            "label": RECOMMENDATION_LABELS[code],
            "reasons": reasons,
        },
        "candidate_turns": candidate_turns,
        "advisory_notice": ADVISORY_NOTICE,
    }


def hr_view(report: dict, transcript: list[dict]) -> dict:
    return {**report, "transcript": transcript}


def candidate_view(report: dict) -> dict:
    # candidate doesn't see the recommendation or weaknesses
    matching = [f for f in report["role_fit"] if f["category"] in (BEST_FIT, SUITABLE, TRAINING)]
    applied = next(f for f in report["role_fit"] if f["role_id"] == report["applied_role_id"])
    return {
        "candidate_name": report["candidate_name"],
        "applied_role": report["applied_role"],
        "generated_at": report["generated_at"],
        "overall_score": report["overall_score"],
        "criteria": [{k: c[k] for k in ("key", "label", "score", "percent")} for c in report["criteria"]],
        "summary": report["summary"],
        "strengths": report["strengths"],
        "improvement_tips": report["improvement_tips"],
        "skills_to_build": applied["gaps"],
        "recommended_roles": [
            {k: f[k] for k in ("role_title", "fit_score", "category", "category_label", "gaps")}
            for f in matching
        ],
        "next_steps": "The hiring team will review your interview and contact you about next steps.",
    }
