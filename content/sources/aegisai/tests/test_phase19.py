"""Tests for Phase 19 — human-in-the-loop response with approval gates.

In-memory SQLite seeded with an agent investigation. Verifies recommendation
generation, the approval gate (no execution without approval), execution via the
mock SOAR provider, verification, and the audit trail.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app import response_engine as engine
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models import AgentInvestigation

sql_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=sql_engine, autocommit=False, autoflush=False)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


_REPORT = {
    "risk_assessment": {"level": "CRITICAL"},
    "executive_summary": "Critical alert investigation.",
    "recommendations": [
        {"action": "Patch immediately", "detail": "Patch CVE-2026-0001 (KEV).", "evidence": "kev_retrieval"},
        {"action": "Escalate for urgent remediation", "detail": "Priority CRITICAL.", "evidence": "risk_score_retrieval"},
        {"action": "Review threat-actor activity / threat hunt", "detail": "APT-X.", "evidence": "misp_intel_retrieval"},
    ],
}


@pytest.fixture(scope="module", autouse=True)
def seed():
    Base.metadata.create_all(bind=sql_engine)
    with TestingSessionLocal() as db:
        db.add(AgentInvestigation(id=1, investigation_type="alert", target="alert:1",
                                  status="completed", confidence=0.9, report=_REPORT))
        db.commit()
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=sql_engine)


client = TestClient(app)


# ── generation ──────────────────────────────────────────────

def test_generate_from_investigation_maps_actions():
    with TestingSessionLocal() as db:
        created = engine.generate_from_investigation(db, 1)
    types = {c["action_type"] for c in created}
    assert {"patch", "escalate", "threat_hunt"} <= types
    assert all(c["status"] == "pending" for c in created)


def test_generation_is_idempotent():
    with TestingSessionLocal() as db:
        again = engine.generate_from_investigation(db, 1)  # already generated
    assert again == []  # no duplicates


def test_generate_unknown_investigation():
    with TestingSessionLocal() as db:
        with pytest.raises(ValueError):
            engine.generate_from_investigation(db, 999)


# ── approval gate (core requirement) ────────────────────────

def _first_pending(db):
    return engine.list_recommendations(db, status="pending")[0]


def test_execute_refused_without_approval():
    with TestingSessionLocal() as db:
        rid = _first_pending(db)["id"]
        with pytest.raises(PermissionError):
            engine.execute(db, rid, "attacker")  # not approved -> refused


def test_verify_refused_without_execution():
    with TestingSessionLocal() as db:
        rid = _first_pending(db)["id"]
        with pytest.raises(PermissionError):
            engine.verify(db, rid)


def test_full_approval_execution_flow_and_audit():
    with TestingSessionLocal() as db:
        rid = _first_pending(db)["id"]
        engine.approve(db, rid, "analyst.jane")
        ex = engine.execute(db, rid, "analyst.jane")
        assert ex["status"] == "executed"
        assert ex["execution_result"]["provider"] == "mock"  # SOAR mock
        vf = engine.verify(db, rid, "analyst.jane")
        assert vf["verified"] is True and vf["status"] == "verified"
        events = [a["event"] for a in engine.audit_trail(db, rid)]
    assert events == ["generated", "approved", "executed", "verified"]


def test_cannot_approve_non_pending():
    with TestingSessionLocal() as db:
        # a verified rec exists from the previous test
        verified = engine.list_recommendations(db, status="verified")[0]
        with pytest.raises(PermissionError):
            engine.approve(db, verified["id"], "someone")


def test_reject_flow():
    with TestingSessionLocal() as db:
        rid = _first_pending(db)["id"]
        r = engine.reject(db, rid, "analyst.jane", "false positive")
    assert r["status"] == "rejected"


# ── API ─────────────────────────────────────────────────────

def test_api_generate_and_list():
    r = client.post("/response/generate", json={"investigation_id": 1})
    assert r.status_code == 200
    lst = client.get("/response/recommendations")
    assert lst.status_code == 200 and len(lst.json()) >= 1


def test_api_execute_without_approval_409():
    pending = client.get("/response/recommendations?status=pending").json()
    if pending:
        rid = pending[0]["id"]
        resp = client.post(f"/response/recommendations/{rid}/execute", json={"actor": "x"})
        assert resp.status_code == 409  # approval gate enforced at the API


def test_api_full_flow():
    pending = client.get("/response/recommendations?status=pending").json()
    assert pending, "expected a pending recommendation"
    rid = pending[0]["id"]
    assert client.post(f"/response/recommendations/{rid}/approve", json={"approver": "jane"}).status_code == 200
    ex = client.post(f"/response/recommendations/{rid}/execute", json={"actor": "jane"})
    assert ex.status_code == 200 and ex.json()["status"] == "executed"
    vf = client.post(f"/response/recommendations/{rid}/verify", json={"actor": "jane"})
    assert vf.status_code == 200 and vf.json()["verified"] is True
    audit = client.get(f"/response/recommendations/{rid}/audit").json()
    assert [a["event"] for a in audit] == ["generated", "approved", "executed", "verified"]


def test_api_stats_and_audit():
    assert client.get("/response/stats").status_code == 200
    assert client.get("/response/audit").status_code == 200
