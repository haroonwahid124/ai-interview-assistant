import pytest

from app.analysis.scoring import CRITERIA_WEIGHTS, criterion_percent, overall_score


def all_criteria(score):
    return {name: score for name in CRITERIA_WEIGHTS}


def test_weights_add_up_to_one():
    assert sum(CRITERIA_WEIGHTS.values()) == pytest.approx(1.0)


@pytest.mark.parametrize("score, expected", [(1, 0), (2, 25), (3, 50), (4, 75), (5, 100)])
def test_criterion_percent_maps_1_to_5_onto_0_to_100(score, expected):
    assert criterion_percent(score) == expected


@pytest.mark.parametrize("bad", [0, 6, -1])
def test_criterion_percent_rejects_out_of_range(bad):
    with pytest.raises(ValueError):
        criterion_percent(bad)


def test_perfect_and_minimum_scores():
    assert overall_score(all_criteria(5)) == 100
    assert overall_score(all_criteria(1)) == 0


def test_weighting_favours_technical_knowledge():
    strong_technical = {"technical_knowledge": 5, "problem_solving": 3, "communication": 3, "behavioural": 3}
    strong_behavioural = {"technical_knowledge": 3, "problem_solving": 3, "communication": 3, "behavioural": 5}
    assert overall_score(strong_technical) > overall_score(strong_behavioural)


def test_known_example():
    # 0.35*75 + 0.25*75 + 0.20*100 + 0.20*50 = 26.25 + 18.75 + 20 + 10 = 75
    criteria = {"technical_knowledge": 4, "problem_solving": 4, "communication": 5, "behavioural": 3}
    assert overall_score(criteria) == 75.0


def test_missing_criterion_is_an_error():
    with pytest.raises(ValueError):
        overall_score({"technical_knowledge": 4})
