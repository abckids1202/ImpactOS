import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import _RATE_LIMITS, app


@pytest.fixture
def client():
    with TestClient(app) as value:
        yield value


@pytest.fixture(autouse=True)
def reset_rate_limits():
    _RATE_LIMITS.clear()
    yield
    _RATE_LIMITS.clear()


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


def test_report_follow_up_correction_and_withdrawal_are_tracked(client: TestClient) -> None:
    login(client, "student@demo.local")
    created = client.post(
        "/api/v1/problem-reports",
        headers=csrf_headers(client),
        json={
            "title": "Follow-up evidence test report",
            "description": "Students regularly cannot find a quiet seat in the library before lunch on school days.",
            "affected_group": "Grade 10 students",
            "scope": "Library",
            "category": "CAMPUS",
            "visibility": "SCHOOL_ANONYMOUS",
        },
    )
    assert created.status_code == 200, created.text
    report_id = created.json()["report"]["id"]
    assert client.post(f"/api/v1/problem-reports/{report_id}/submit", headers=csrf_headers(client)).status_code == 200
    added = client.post(
        f"/api/v1/problem-reports/{report_id}/follow-up-evidence",
        headers=csrf_headers(client),
        json={"source": "Second observation sheet", "relevance": "The same pattern occurred on another school day.", "visibility": "TEAM"},
    )
    assert added.status_code == 200, added.text
    assert added.json()["follow_up_evidence"][0]["source"] == "Second observation sheet"
    corrected = client.post(
        f"/api/v1/problem-reports/{report_id}/request-correction",
        headers=csrf_headers(client),
        json={"decision": "REQUEST_CORRECTION", "reason": "I need to clarify the observation period before publication."},
    )
    assert corrected.status_code == 200, corrected.text
    assert corrected.json()["status"] == "CHANGES_REQUESTED"
    withdrawn = client.post(f"/api/v1/problem-reports/{report_id}/withdraw", headers=csrf_headers(client))
    assert withdrawn.status_code == 200, withdrawn.text
    assert withdrawn.json()["status"] == "WITHDRAWN"


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


def test_public_site_and_story_serializer_are_allowlisted(client: TestClient) -> None:
    site = client.get("/api/v1/public/site")
    assert site.status_code == 200
    assert site.json()["product"] == "Pilar Impact Lab"
    assert site.json()["powered_by"] == "ImpactOS"
    stories = client.get("/api/v1/public/impact-stories")
    assert stories.status_code == 200
    assert stories.json()["items"]
    forbidden = {"id", "school_id", "source_project_id", "approved_by", "published_by", "raw_report", "email"}
    assert forbidden.isdisjoint(stories.json()["items"][0])


def test_unauthenticated_workspace_endpoint_is_protected(client: TestClient) -> None:
    response = client.get("/api/v1/problem-clusters")
    assert response.status_code == 401


def test_invitation_is_single_use_and_assigns_controlled_role(client: TestClient) -> None:
    login(client, "admin@demo.local")
    email = f"alpha-{uuid4().hex[:10]}@example.test"
    created = client.post(
        "/api/v1/admin/invitations",
        headers=csrf_headers(client),
        json={"email": email, "role": "MENTOR", "expires_in_days": 2},
    )
    assert created.status_code == 200, created.text
    raw_token = created.json()["token"]
    preview = client.get(f"/api/v1/invitations/{raw_token}/preview")
    assert preview.status_code == 200
    assert preview.json()["role"] == "MENTOR"
    accepted = client.post(
        f"/api/v1/invitations/{raw_token}/accept",
        json={"display_name": "Alpha Mentor", "password": "alpha-password-123"},
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["user"]["role"] == "MENTOR"
    assert client.get("/api/v1/invitations/{}/preview".format(raw_token)).status_code == 410
    assert client.post("/api/v1/auth/login", json={"email": email, "password": "alpha-password-123"}).status_code == 200


def test_demo_accounts_are_disabled_outside_demo(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    monkeypatch.setenv("APP_MODE", "PRODUCTION")
    response = client.post("/api/v1/auth/login", json={"email": "student@demo.local", "password": "demo1234"})
    assert response.status_code == 401


def test_public_story_requires_approval_and_can_be_withdrawn(client: TestClient) -> None:
    login(client, "admin@demo.local")
    slug = f"alpha-story-{uuid4().hex[:8]}"
    created = client.post(
        "/api/v1/admin/public-impact-stories",
        headers=csrf_headers(client),
        json={
            "slug": slug,
            "title": "A reviewed synthetic story",
            "problem_summary": "A synthetic problem summary.",
            "intervention_summary": "A synthetic intervention.",
            "measurement_summary": "A declared before and after measure.",
            "observed_result": "An observed mixed result.",
            "limitations": "Synthetic data only.",
            "result_type": "MIXED",
            "is_synthetic": True,
        },
    )
    assert created.status_code == 200, created.text
    story_id = created.json()["id"]
    assert client.get(f"/api/v1/public/impact-stories/{slug}").status_code == 404
    for action in ("submit-review", "approve", "publish"):
        response = client.post(f"/api/v1/admin/public-impact-stories/{story_id}/{action}", headers=csrf_headers(client))
        assert response.status_code == 200, response.text
    assert client.get(f"/api/v1/public/impact-stories/{slug}").status_code == 200
    withdrawn = client.post(f"/api/v1/admin/public-impact-stories/{story_id}/withdraw", headers=csrf_headers(client))
    assert withdrawn.status_code == 200
    assert client.get(f"/api/v1/public/impact-stories/{slug}").status_code == 404
