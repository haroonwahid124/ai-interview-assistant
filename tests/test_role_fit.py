from app.reports.generator import recommend
from app.role_fit.engine import (
    BEST_FIT, NOT_SUITABLE, SUITABLE, TRAINING, fit_for_role, rank_roles,
)

BACKEND = [
    {"name": "REST APIs", "weight": 3, "required_level": 4, "critical": True},
    {"name": "Databases & SQL", "weight": 1, "required_level": 4, "critical": False},
]


def test_meeting_every_requirement_is_100_percent():
    fit = fit_for_role(1, "Backend", BACKEND, {"rest apis": 4, "databases & sql": 4})
    assert fit.fit_score == 100
    assert fit.category == SUITABLE
    assert fit.gaps == []


def test_exceeding_a_requirement_gives_no_bonus():
    fit = fit_for_role(1, "Backend", BACKEND, {"rest apis": 5, "databases & sql": 0})
    # APIs fully covered (weight 3), SQL not at all (weight 1) -> 3/4
    assert fit.fit_score == 75.0


def test_missing_skill_counts_as_zero():
    fit = fit_for_role(1, "Backend", BACKEND, {})
    assert fit.fit_score == 0
    assert fit.category == NOT_SUITABLE
    assert {g.skill for g in fit.gaps} == {"REST APIs", "Databases & SQL"}


def test_critical_gap_blocks_suitable_even_with_high_score():
    requirements = [
        {"name": "A", "weight": 1, "required_level": 5, "critical": True},
        {"name": "B", "weight": 9, "required_level": 1, "critical": False},
    ]
    fit = fit_for_role(1, "Role", requirements, {"a": 3, "b": 5})
    assert fit.fit_score >= 75
    assert fit.category == TRAINING
    assert [g.skill for g in fit.critical_gaps] == ["A"]


def test_skill_names_match_case_insensitively():
    fit = fit_for_role(1, "Backend", BACKEND, {"REST APIs".lower(): 4, "databases & sql": 4})
    assert fit.fit_score == 100


def test_only_one_best_fit_and_it_is_the_top_suitable_role():
    roles = [
        {"id": 1, "title": "Backend", "skills": BACKEND},
        {"id": 2, "title": "API only", "skills": [BACKEND[0]]},
        {"id": 3, "title": "Designer", "skills": [{"name": "Figma", "weight": 1, "required_level": 3, "critical": True}]},
    ]
    ranked = rank_roles(roles, {"rest apis": 4, "databases & sql": 3})
    categories = [r.category for r in ranked]
    assert categories.count(BEST_FIT) == 1
    assert ranked[0].role_title == "API only"          # 100% beats 93.8%
    assert ranked[1].category == SUITABLE
    assert ranked[-1].category == NOT_SUITABLE


def test_no_best_fit_when_nothing_is_suitable():
    roles = [{"id": 1, "title": "Backend", "skills": BACKEND}]
    ranked = rank_roles(roles, {"rest apis": 1})
    assert ranked[0].category != BEST_FIT


# recommendation rules

def good_fit():
    return fit_for_role(1, "Backend", BACKEND, {"rest apis": 4, "databases & sql": 4})


def weak_fit():
    return fit_for_role(1, "Backend", BACKEND, {"rest apis": 1})


def test_strong_candidate_is_strongly_recommended():
    code, _ = recommend(85, good_fit(), candidate_turns=6)
    assert code == "strongly_recommend"


def test_good_score_with_good_fit_is_consider():
    code, _ = recommend(70, good_fit(), candidate_turns=6)
    assert code == "consider"


def test_high_score_but_poor_fit_is_not_strongly_recommended():
    code, reasons = recommend(90, weak_fit(), candidate_turns=6)
    assert code == "further_interview"
    assert any("Critical gap" in r for r in reasons)


def test_weak_candidate_is_not_recommended():
    code, _ = recommend(30, weak_fit(), candidate_turns=6)
    assert code == "not_recommended"


def test_too_few_answers_always_needs_further_interview():
    code, reasons = recommend(95, good_fit(), candidate_turns=1)
    assert code == "further_interview"
    assert "not enough evidence" in reasons[0]
