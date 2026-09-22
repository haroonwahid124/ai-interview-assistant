"""
Role-fit engine: how well does the candidate match each role?

For every skill a role needs we compare the level the candidate showed with
the level the role requires:

    coverage = min(candidate_level / required_level, 1)

A role's fit is the weighted average coverage, as a percentage. Exceeding a
requirement doesn't earn extra credit, so strength in one area can't hide a
gap in another.

Categories:
    best_fit      the single highest-scoring role that is also "suitable"
    suitable      fit >= 75% and no critical gaps
    training      fit >= 50%, or >= 75% but with a critical gap
    not_suitable  fit < 50%
"""
from dataclasses import asdict, dataclass, field

SUITABLE_THRESHOLD = 75.0
TRAINING_THRESHOLD = 50.0

BEST_FIT = "best_fit"
SUITABLE = "suitable"
TRAINING = "training"
NOT_SUITABLE = "not_suitable"

CATEGORY_LABELS = {
    BEST_FIT: "Best fit",
    SUITABLE: "Suitable",
    TRAINING: "Possible with training",
    NOT_SUITABLE: "Not suitable",
}


@dataclass
class SkillGap:
    skill: str
    candidate_level: int
    required_level: int
    critical: bool


@dataclass
class RoleFit:
    role_id: int
    role_title: str
    fit_score: float
    category: str
    gaps: list[SkillGap] = field(default_factory=list)

    @property
    def critical_gaps(self) -> list[SkillGap]:
        return [g for g in self.gaps if g.critical]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["category_label"] = CATEGORY_LABELS[self.category]
        return data


def fit_for_role(role_id: int, role_title: str, requirements: list[dict], levels: dict[str, int]) -> RoleFit:
    """
    requirements: the role's skills, e.g. [{"name": "SQL", "weight": 2, "required_level": 4, "critical": True}]
    levels: candidate skill levels keyed by lower-case skill name, e.g. {"sql": 3}
    """
    total_weight = 0.0
    weighted_coverage = 0.0
    gaps: list[SkillGap] = []

    for req in requirements:
        weight = float(req.get("weight", 1))
        required = int(req.get("required_level", 3))
        have = int(levels.get(req["name"].lower(), 0))

        total_weight += weight
        weighted_coverage += weight * min(have / required, 1.0)

        if have < required:
            gaps.append(SkillGap(req["name"], have, required, bool(req.get("critical", False))))

    fit = round(weighted_coverage / total_weight * 100, 1) if total_weight else 0.0
    # Biggest shortfalls first, critical ones before the rest.
    gaps.sort(key=lambda g: (not g.critical, g.candidate_level - g.required_level))

    has_critical_gap = any(g.critical for g in gaps)
    if fit >= SUITABLE_THRESHOLD and not has_critical_gap:
        category = SUITABLE
    elif fit >= TRAINING_THRESHOLD:
        category = TRAINING
    else:
        category = NOT_SUITABLE

    return RoleFit(role_id, role_title, fit, category, gaps)


def rank_roles(roles: list[dict], levels: dict[str, int]) -> list[RoleFit]:
    """
    roles: [{"id", "title", "skills"}]
    Returns every role sorted best first, with the top suitable role marked best_fit.
    """
    results = [fit_for_role(r["id"], r["title"], r["skills"], levels) for r in roles]
    # Suitable roles first, then by fit score. Title breaks ties so output is stable.
    order = {SUITABLE: 0, TRAINING: 1, NOT_SUITABLE: 2}
    results.sort(key=lambda r: (order[r.category], -r.fit_score, r.role_title))

    if results and results[0].category == SUITABLE:
        results[0].category = BEST_FIT
    return results
