import pytest
from fastapi.testclient import TestClient

from app.main import _RATE_LIMITS, app


@pytest.fixture(autouse=True)
def reset_rate_limits():
    _RATE_LIMITS.clear()
    yield
    _RATE_LIMITS.clear()


@pytest.fixture
def client():
    with TestClient(app) as value:
        yield value


def csrf_headers(client: TestClient) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("impactos_csrf", "")}


def login(client: TestClient, email: str) -> dict:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "demo1234"})
    assert response.status_code == 200, response.text
    return response.json()


def test_dashboard_is_role_aware_and_does_not_leak_restricted_records(client: TestClient) -> None:
    expected = {
        "student@demo.local": "STUDENT_CONTRIBUTOR",
        "leader@demo.local": "STUDENT_PROJECT_LEADER",
        "mentor@demo.local": "MENTOR",
        "osis@demo.local": "OSIS_REVIEWER",
        "moderator@demo.local": "MODERATOR",
        "admin@demo.local": "ADMINISTRATOR",
    }
    for email, role in expected.items():
        login(client, email)
        response = client.get("/api/v1/dashboard")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["viewer"]["active_workspace"] == role
        assert data["viewer"]["roles"][0]["label"]
        if role == "OSIS_REVIEWER":
            assert all(item["status"] == "VALIDATED" for item in data["role_sections"]["validated_problems"])
            assert all("Private synthetic" not in str(item) for item in data["role_sections"].values())
        if role == "MODERATOR":
            assert data["role_sections"]["restricted_reports"]
        if role == "MENTOR":
            assert any(item["id"] == "research-canteen" for item in data["role_sections"]["reviews_awaiting_attention"])


def test_student_can_follow_and_unfollow_a_problem(client: TestClient) -> None:
    login(client, "student@demo.local")
    detail = client.get("/api/v1/problems/cluster-canteen")
    assert detail.status_code == 200
    assert detail.json()["followed"] is True
    unfollowed = client.delete("/api/v1/problems/cluster-canteen/follow", headers=csrf_headers(client))
    assert unfollowed.status_code == 200
    assert unfollowed.json()["followed"] is False
    followed = client.post("/api/v1/problems/cluster-canteen/follow", headers=csrf_headers(client))
    assert followed.status_code == 200
    assert followed.json()["followed"] is True


def test_student_report_enters_moderation_and_moderator_decision_changes_state(client: TestClient) -> None:
    login(client, "student@demo.local")
    created = client.post("/api/v1/problem-reports", headers=csrf_headers(client), json={"title": "Queue feels crowded near the second break", "description": "This synthetic report describes a recurring queue pattern for role-workspace testing only.", "affected_group": "Students", "scope": "Main canteen", "category": "FACILITIES", "frequency": "Most school days", "visibility": "SCHOOL_ANONYMOUS"})
    assert created.status_code == 200, created.text
    report_id = created.json()["report"]["id"]
    submitted = client.post(f"/api/v1/problem-reports/{report_id}/submit", headers=csrf_headers(client))
    assert submitted.status_code == 200
    assert submitted.json()["report"]["status"] == "MODERATION_REVIEW"

    client.post("/api/v1/auth/logout", headers=csrf_headers(client))
    login(client, "moderator@demo.local")
    queue = client.get("/api/v1/moderation/reports")
    assert queue.status_code == 200
    assert any(item["id"] == report_id for item in queue.json()["visibility"])
    detail = client.get(f"/api/v1/moderation/reports/{report_id}")
    assert detail.status_code == 200
    decision = client.post(f"/api/v1/moderation/reports/{report_id}/decision", headers=csrf_headers(client), json={"decision": "RETURN_FOR_CLARIFICATION", "reason": "Please add a clearer observation window."})
    assert decision.status_code == 200, decision.text
    assert decision.json()["status"] == "CHANGES_REQUESTED"


def test_osis_can_prioritize_and_draft_update_but_cannot_see_restricted_reports(client: TestClient) -> None:
    login(client, "osis@demo.local")
    priorities = client.get("/api/v1/osis/priorities")
    assert priorities.status_code == 200
    assert priorities.json()["items"]
    updated = client.post("/api/v1/osis/problems/cluster-canteen/priority", headers=csrf_headers(client), json={"priority": "HIGH", "rationale": "The validated synthetic signals affect a repeated daily school experience."})
    assert updated.status_code == 200, updated.text
    assert updated.json()["priority"] == "HIGH"
    draft = client.post("/api/v1/problem-clusters/cluster-canteen/official-updates", headers=csrf_headers(client), json={"status": "DRAFT", "message": "OSIS is reviewing the validated canteen queue pattern; no intervention result has been claimed."})
    assert draft.status_code == 200, draft.text
    assert draft.json()["official_updates"][0]["status"] == "DRAFT"
    assert client.get("/api/v1/moderation/reports/report-canteen-7").status_code == 403


def test_leader_can_complete_owned_task_and_other_student_cannot_update_it(client: TestClient) -> None:
    login(client, "leader@demo.local")
    tasks = client.get("/api/v1/tasks/mine")
    assert tasks.status_code == 200
    task = next(item for item in tasks.json()["items"] if item["id"] == "task-canteen-schedule")
    updated = client.patch(f"/api/v1/tasks/{task['id']}", headers=csrf_headers(client), json={"status": "COMPLETED"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "COMPLETED"
    client.post("/api/v1/auth/logout", headers=csrf_headers(client))
    login(client, "student@demo.local")
    assert client.patch(f"/api/v1/tasks/{task['id']}", headers=csrf_headers(client), json={"status": "COMPLETED"}).status_code in {403, 404}


def test_search_respects_role_visibility(client: TestClient) -> None:
    login(client, "osis@demo.local")
    response = client.get("/api/v1/search?q=private%20synthetic")
    assert response.status_code == 200
    assert response.json()["items"] == []

    client.post("/api/v1/auth/logout", headers=csrf_headers(client))
    login(client, "moderator@demo.local")
    response = client.get("/api/v1/search?q=private%20synthetic")
    assert response.status_code == 200
    assert any(item["id"] == "report-canteen-7" for item in response.json()["items"])


def test_member_feedback_is_safe_and_admin_managed(client: TestClient) -> None:
    login(client, "student@demo.local")
    created = client.post("/api/v1/feedback", headers=csrf_headers(client), json={"category": "CONFUSING", "description": "The next step on the report page could be clearer.", "severity": "LOW", "route": "/app/reports", "user_role": "Student contributor", "browser": "test browser", "screen_size": "390x844", "app_version": "0.1.0"})
    assert created.status_code == 200, created.text
    feedback_id = created.json()["feedback"]["id"]
    assert "session" not in created.text.lower()

    client.post("/api/v1/auth/logout", headers=csrf_headers(client))
    login(client, "admin@demo.local")
    listing = client.get("/api/v1/admin/feedback")
    assert listing.status_code == 200
    assert any(item["id"] == feedback_id for item in listing.json())
    updated = client.patch(f"/api/v1/admin/feedback/{feedback_id}", headers=csrf_headers(client), json={"status": "TRIAGED"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "TRIAGED"


def test_response_loop_commitment_is_visible_and_requires_completion_evidence(client: TestClient) -> None:
    login(client, "osis@demo.local")
    detail = client.get("/api/v1/problems/cluster-canteen")
    assert detail.status_code == 200
    assert detail.json()["response_commitments"]
    assert detail.json()["response_loop"]["next_step"]

    created = client.post(
        "/api/v1/response-commitments",
        headers=csrf_headers(client),
        json={
            "cluster_id": "cluster-canteen",
            "title": "Confirm the next canteen pilot decision",
            "intended_outcome": "Publish a safe decision after the baseline is reviewed.",
            "owner_role": "OSIS_REVIEWER",
            "owner_id": "user-osis",
            "priority": "HIGH",
            "due_date": "2026-09-10",
            "next_update_date": "2026-09-03",
        },
    )
    assert created.status_code == 200, created.text
    commitment_id = created.json()["id"]
    assert created.json()["status"] == "OPEN"
    assert client.post(f"/api/v1/response-commitments/{commitment_id}/complete", headers=csrf_headers(client), json={"completion_note": "The decision was recorded for the pilot team."}).status_code == 200

    client.post("/api/v1/auth/logout", headers=csrf_headers(client))
    login(client, "student@demo.local")
    work = client.get("/api/v1/work")
    assert work.status_code == 200
    assert all(item["id"] != commitment_id for item in work.json()["items"])


def test_priority_assessment_and_not_now_guard_are_explicit(client: TestClient) -> None:
    login(client, "osis@demo.local")
    assessed = client.post(
        "/api/v1/problems/cluster-assessment/priority-assessment",
        headers=csrf_headers(client),
        json={"priority": "HIGH", "evidence_strength": 4, "urgency_score": 3, "reach_score": 5, "feasibility_score": 4, "rationale": "The evidence is repeated and the school can test a practical response.", "review_date": "2026-09-12"},
    )
    assert assessed.status_code == 200, assessed.text
    assert assessed.json()["priority_assessment"]["evidence_strength"] == 4
    assert assessed.json()["priority_assessment"]["reach_score"] == 5

    created = client.post(
        "/api/v1/response-commitments",
        headers=csrf_headers(client),
        json={"cluster_id": "cluster-assessment", "title": "Review the assessment calendar option", "owner_role": "OSIS_REVIEWER", "owner_id": "user-osis", "next_update_date": "2026-09-04"},
    )
    assert created.status_code == 200, created.text
    commitment_id = created.json()["id"]
    missing_reason = client.patch(f"/api/v1/response-commitments/{commitment_id}", headers=csrf_headers(client), json={"status": "NOT_NOW"})
    assert missing_reason.status_code == 422
    changed = client.patch(f"/api/v1/response-commitments/{commitment_id}", headers=csrf_headers(client), json={"status": "NOT_NOW", "reason": "The school calendar is being finalized first.", "next_update_date": "2026-09-20"})
    assert changed.status_code == 200, changed.text
    assert changed.json()["status"] == "NOT_NOW"


def test_unified_work_and_timeline_keep_the_two_lanes_distinct(client: TestClient) -> None:
    login(client, "osis@demo.local")
    work = client.get("/api/v1/work")
    assert work.status_code == 200
    assert work.json()["manager_view"] is True
    assert any(item["type"] == "RESPONSE_COMMITMENT" for item in work.json()["items"])
    cluster_work = client.get("/api/v1/problems/cluster-canteen/work")
    assert cluster_work.status_code == 200
    assert cluster_work.json()["commitments"]
    assert all(item["type"] == "PROJECT_TASK" for item in cluster_work.json()["project_tasks"])
    timeline = client.get("/api/v1/problems/cluster-canteen/timeline")
    assert timeline.status_code == 200
    assert any(item["type"] in {"COMMITMENT_UPDATE", "COMMITMENT_STATUS"} for item in timeline.json()["items"])


def test_team_commitment_details_do_not_leak_into_student_timeline(client: TestClient) -> None:
    login(client, "osis@demo.local")
    created = client.post(
        "/api/v1/response-commitments",
        headers=csrf_headers(client),
        json={
            "cluster_id": "cluster-canteen",
            "title": "Restricted response handoff",
            "intended_outcome": "Coordinate a reviewer-only decision.",
            "owner_role": "MENTOR",
            "owner_id": "user-mentor",
            "visibility": "TEAM",
            "next_update_date": "2026-09-15",
        },
    )
    assert created.status_code == 200, created.text
    commitment_id = created.json()["id"]
    update = client.post(
        f"/api/v1/response-commitments/{commitment_id}/updates",
        headers=csrf_headers(client),
        json={"kind": "DECISION", "message": "Reviewer-only handoff detail.", "visibility": "TEAM"},
    )
    assert update.status_code == 200, update.text
    client.post("/api/v1/auth/logout", headers=csrf_headers(client))
    login(client, "student@demo.local")
    timeline = client.get("/api/v1/problems/cluster-canteen/timeline")
    assert timeline.status_code == 200
    assert all(item["message"] != "Reviewer-only handoff detail." for item in timeline.json()["items"])
