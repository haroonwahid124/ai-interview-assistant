# role fit = weighted avg of min(candidate_level / required_level, 1) per skill
# suitable: >= 75% and no critical gaps, training: >= 50%, else not suitable
# best_fit is the top suitable role
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
    # levels is keyed by lowercase skill name, e.g. {"sql": 3}
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
    # critical gaps first, then biggest gap
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
    results = [fit_for_role(r["id"], r["title"], r["skills"], levels) for r in roles]
    # sort by category, then score, then title
    order = {SUITABLE: 0, TRAINING: 1, NOT_SUITABLE: 2}
    results.sort(key=lambda r: (order[r.category], -r.fit_score, r.role_title))

    if results and results[0].category == SUITABLE:
        results[0].category = BEST_FIT
    return results
