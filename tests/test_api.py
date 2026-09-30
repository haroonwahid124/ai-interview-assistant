# API tests (mock evaluator, no network)
from app.schemas import SessionConfig

STRONG_TRANSCRIPT = [
    {"role": "interviewer", "text": "Tell me about yourself."},
    {"role": "candidate", "text": "I'm a final-year student. I build REST APIs in Python with FastAPI and Java with Spring."},
    {"role": "interviewer", "text": "Tell me about an API you built."},
    {"role": "candidate", "text": "I designed a JSON API with HTTP endpoints backed by a Postgres database. "
                                  "I wrote SQL queries, added an index, and used a join to cut response time."},
    {"role": "interviewer", "text": "How would you approach a slow endpoint?"},
    {"role": "candidate", "text": "First I would measure, because guessing wastes time. Then I would add a cache, "
                                  "so repeated queries are cheap. The trade-off is stale data, so I'd pick an expiry."},
    {"role": "interviewer", "text": "Tell me about a disagreement."},
    {"role": "candidate", "text": "My team disagreed about testing. We listened to each other, agreed on unit tests "
                                  "with pytest in CI, and I learned to give feedback kindly."},
]


def role_id(client, title):
    return next(r["id"] for r in client.get("/api/roles").json() if r["title"] == title)


def create_interview(client, title="Backend Developer", name="Test Candidate"):
    res = client.post("/api/interviews", json={"role_id": role_id(client, title), "candidate_name": name})
    assert res.status_code == 201, res.text
    return res.json()["id"]


def test_starter_roles_are_seeded(client):
    titles = {r["title"] for r in client.get("/api/roles").json()}
    assert {"Software Engineer", "Backend Developer", "Data Engineer", "UI/UX Designer"} <= titles


def test_create_role_validates_input(client):
    res = client.post("/api/roles", json={"title": "Empty", "skills": []})
    assert res.status_code == 422

    res = client.post("/api/roles", json={
        "title": "QA Engineer",
        "skills": [{"name": "Testing", "weight": 2, "required_level": 4, "critical": True}],
    })
    assert res.status_code == 201
    assert client.post("/api/roles", json={
        "title": "QA Engineer", "skills": [{"name": "Testing"}],
    }).status_code == 409


def test_unknown_role_or_interview_returns_404(client):
    assert client.post("/api/interviews", json={"role_id": 9999, "candidate_name": "X"}).status_code == 404
    assert client.get("/api/interviews/not-a-real-id").status_code == 404


def test_session_config_contains_prompt_and_tool(client, monkeypatch):
    monkeypatch.setattr("app.interview.session.get_voice_agent_token", lambda: "fake-token")
    interview_id = create_interview(client, name="Ada Lovelace")

    res = client.post(f"/api/interviews/{interview_id}/session")
    assert res.status_code == 200
    config = SessionConfig.model_validate(res.json())
    assert config.token == "fake-token"
    assert "Backend Developer" in config.session["system_prompt"]
    assert config.session["greeting"].startswith("Hi Ada")
    assert config.session["tools"][0]["name"] == "end_interview"


def test_transcript_without_candidate_answers_is_rejected(client):
    interview_id = create_interview(client)
    res = client.post(f"/api/interviews/{interview_id}/transcript",
                      json={"turns": [{"role": "interviewer", "text": "Hello?"}]})
    assert res.status_code == 422
    assert "No candidate answers" in res.json()["detail"]


def test_full_flow_produces_hr_and_candidate_reports(client, monkeypatch):
    interview_id = create_interview(client)

    res = client.post(f"/api/interviews/{interview_id}/transcript", json={"turns": STRONG_TRANSCRIPT})
    assert res.status_code == 200, res.text
    summary = res.json()
    assert summary["status"] == "completed"
    assert 0 <= summary["overall_score"] <= 100
    assert summary["recommendation"]

    hr = client.get(f"/api/interviews/{interview_id}/report/hr").json()
    assert len(hr["criteria"]) == 4
    assert len(hr["role_fit"]) >= 4
    assert sum(1 for f in hr["role_fit"] if f["category"] == "best_fit") <= 1
    assert hr["recommendation"]["reasons"]
    assert [t["text"] for t in hr["transcript"]] == [t["text"] for t in STRONG_TRANSCRIPT]
    # The designer role should rank below the backend role for this transcript.
    order = [f["role_title"] for f in hr["role_fit"]]
    assert order.index("Backend Developer") < order.index("UI/UX Designer")

    candidate = client.get(f"/api/interviews/{interview_id}/report/candidate").json()
    assert "recommendation" not in candidate
    assert "weaknesses" not in candidate
    assert "transcript" not in candidate
    assert all(r["category"] != "not_suitable" for r in candidate["recommended_roles"])

    # A completed interview can't be restarted or overwritten.
    monkeypatch.setattr("app.interview.session.get_voice_agent_token", lambda: "fake-token")
    assert client.post(f"/api/interviews/{interview_id}/session").status_code == 409
    assert client.post(f"/api/interviews/{interview_id}/transcript",
                       json={"turns": STRONG_TRANSCRIPT}).status_code == 422


def test_failed_scoring_keeps_transcript_and_can_be_retried(client, monkeypatch):
    from app.analysis.llm_client import EvaluationError, MockEvaluator

    class Broken:
        def evaluate(self, *args):
            raise EvaluationError("model unavailable")

    interview_id = create_interview(client)
    monkeypatch.setattr("app.interview.session.get_evaluator", lambda: Broken())
    res = client.post(f"/api/interviews/{interview_id}/transcript", json={"turns": STRONG_TRANSCRIPT})
    assert res.status_code == 502
    assert client.get(f"/api/interviews/{interview_id}").json()["status"] == "failed"

    monkeypatch.setattr("app.interview.session.get_evaluator", lambda: MockEvaluator())
    res = client.post(f"/api/interviews/{interview_id}/evaluate")
    assert res.status_code == 200
    assert res.json()["status"] == "completed"


def test_interview_list_shows_scores(client):
    rows = client.get("/api/interviews").json()
    assert any(r["status"] == "completed" and r["overall_score"] is not None for r in rows)
