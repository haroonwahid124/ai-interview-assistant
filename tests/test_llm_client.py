from app.analysis.llm_client import _inline_refs, normalise_skills
from app.schemas import CriteriaScores, CriterionScore, Evaluation, SkillEvidence


def make_eval(skills):
    c = CriterionScore(score=3, evidence="x")
    return Evaluation(
        criteria=CriteriaScores(technical_knowledge=c, problem_solving=c, communication=c, behavioural=c),
        skills=skills, strengths=[], weaknesses=[], improvement_tips=[], summary="",
    )


def test_normalise_skills_fixes_case_drops_unknown_and_fills_missing():
    evaluation = make_eval([
        SkillEvidence(skill="rest apis", level=4, evidence="built APIs"),
        SkillEvidence(skill="Juggling", level=5, evidence="made up"),
        SkillEvidence(skill="REST APIs", level=1, evidence="duplicate, ignored"),
    ])
    result = normalise_skills(evaluation, ["REST APIs", "Databases & SQL"])
    assert [(s.skill, s.level) for s in result.skills] == [("REST APIs", 4), ("Databases & SQL", 0)]


def test_inline_refs_removes_all_refs():
    schema = _inline_refs(Evaluation.model_json_schema())
    assert "$defs" not in schema
    assert "$ref" not in str(schema)
    assert schema["properties"]["criteria"]["properties"]["communication"]["properties"]["score"]["maximum"] == 5
