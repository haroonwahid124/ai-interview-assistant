# weights add up to 1
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
    # 1-5 -> 0-100. (score-1)/4 so the lowest score is 0% not 20%
    if not 1 <= score <= 5:
        raise ValueError(f"Criterion score must be 1-5, got {score}")
    return (score - 1) / 4 * 100


def overall_score(criteria: dict[str, int]) -> float:
    missing = CRITERIA_WEIGHTS.keys() - criteria.keys()
    if missing:
        raise ValueError(f"Missing criteria: {sorted(missing)}")
    total = sum(weight * criterion_percent(criteria[name]) for name, weight in CRITERIA_WEIGHTS.items())
    return round(total, 1)
