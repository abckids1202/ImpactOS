import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as value:
        yield value


def csrf_headers(client: TestClient) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("impactos_csrf", "")}


def login(client: TestClient, email: str) -> None:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "demo1234"})
    assert response.status_code == 200, response.text


def test_health_and_demo_login(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["synthetic_data"] is True
    login(client, "student@demo.local")
    assert client.get("/api/v1/me").json()["role"] == "STUDENT"


def test_role_boundary_blocks_admin_audit(client: TestClient) -> None:
    login(client, "student@demo.local")
    response = client.get("/api/v1/admin/audit-logs")
    assert response.status_code == 403


def test_normal_problem_submission_enters_moderation(client: TestClient) -> None:
    login(client, "student@demo.local")
    created = client.post(
        "/api/v1/problem-reports",
        headers=csrf_headers(client),
        json={
            "title": "Library seats fill before lunch",
            "description": "Students regularly cannot find a quiet seat in the library before lunch on school days.",
            "affected_group": "Grade 10 students",
            "scope": "Library",
            "category": "CAMPUS",
            "frequency": "Most school days",
            "severity": "MEDIUM",
            "visibility": "SCHOOL_NAMED",
        },
    )
    assert created.status_code == 200, created.text
    report_id = created.json()["report"]["id"]
    submitted = client.post(f"/api/v1/problem-reports/{report_id}/submit", headers=csrf_headers(client))
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["report"]["status"] == "MODERATION_REVIEW"


def test_sensitive_problem_never_enters_public_feed(client: TestClient) -> None:
    login(client, "student@demo.local")
    created = client.post(
        "/api/v1/problem-reports",
        headers=csrf_headers(client),
        json={
            "title": "Private bullying concern",
            "description": "A student reports bullying and needs the designated safeguarding team to review it.",
            "affected_group": "One student",
            "scope": "Private",
            "category": "WELLBEING",
            "visibility": "SCHOOL_NAMED",
        },
    )
    assert created.status_code == 200
    report_id = created.json()["report"]["id"]
    submitted = client.post(f"/api/v1/problem-reports/{report_id}/submit", headers=csrf_headers(client))
    assert submitted.status_code == 200
    assert submitted.json()["report"]["status"] == "PRIVATE_REVIEW"
    clusters = client.get("/api/v1/problem-clusters").json()
    assert all(item["title"] != "Private bullying concern" for item in clusters)


def test_anonymous_survey_response_and_safe_analysis(client: TestClient) -> None:
    public = client.get("/api/v1/public/surveys/demo-assessment")
    assert public.status_code == 200
    question_id = public.json()["questions"][0]["id"]
    response = client.post(
        "/api/v1/public/surveys/demo-assessment/responses",
        json={"idempotency_key": "test-anonymous-response-1", "answers": {question_id: "Often"}},
    )
    assert response.status_code == 200
    assert client.post(
        "/api/v1/public/surveys/demo-assessment/responses",
        json={"idempotency_key": "test-anonymous-response-1", "answers": {question_id: "Often"}},
    ).json()["status"] == "already_received"
    login(client, "leader@demo.local")
    analysis = client.get("/api/v1/surveys/survey-assessment/analysis")
    assert analysis.status_code == 200
    export = client.get("/api/v1/surveys/survey-assessment/export")
    assert export.status_code == 200
    assert "student@demo.local" not in export.text


def test_activation_requires_primary_metric_and_baseline(client: TestClient) -> None:
    login(client, "student@demo.local")
    response = client.post("/api/v1/impact-projects/impact-study-space/activate", headers=csrf_headers(client))
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "BASELINE_REQUIRED"
