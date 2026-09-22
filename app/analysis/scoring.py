"""
Overall score from the four criterion scores.

Pure functions only: no database, no LLM. That's what makes them easy to test.
"""

# How much each criterion counts towards the overall score. Must add up to 1.
CRITERIA_WEIGHTS: dict[str, float] = {
    "technical_knowledge": 0.35,
    "problem_solving": 0.25,
    "communication": 0.20,
    "behavioural": 0.20,
}

CRITERIA_LABELS: dict[str, str] = {
    "technical_knowledge": "Technical knowledge",
    "problem_solving": "Problem solving",
    "communication": "Communication",
    "behavioural": "Behavioural",
}


def criterion_percent(score: int) -> float:
    """Map a 1-5 score onto 0-100.

    We use (score - 1) / 4 rather than score / 5, because on a 1-5 scale
    the lowest possible answer is 1. With score / 5 a candidate who scored
    the minimum everywhere would still get 20%.
    """
    if not 1 <= score <= 5:
        raise ValueError(f"Criterion score must be 1-5, got {score}")
    return (score - 1) / 4 * 100


def overall_score(criteria: dict[str, int]) -> float:
    """Weighted average of the criterion scores, as a percentage rounded to 1 dp."""
    missing = CRITERIA_WEIGHTS.keys() - criteria.keys()
    if missing:
        raise ValueError(f"Missing criteria: {sorted(missing)}")
    total = sum(weight * criterion_percent(criteria[name]) for name, weight in CRITERIA_WEIGHTS.items())
    return round(total, 1)
