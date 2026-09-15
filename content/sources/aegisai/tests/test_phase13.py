"""Tests for Phase 13 — AI Threat Analyst.

In-memory SQLite seeded with CTI + graph + Wazuh data; the analyst runs in
deterministic (no-LLM) mode so answers are reproducible and grounded.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.ai import query_router
from backend.app.ai.providers import get_provider
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models import (
    CVE,
    CorrelationResult,
    CTIRelationship,
    EPSSScore,
    GraphMetric,
    KEVEntry,
    PriorityScore,
    RiskScore,
    Technique,
    ThreatActor,
    WazuhAlert,
    WazuhAlertEnrichment,
)

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def seed():
    Base.metadata.create_all(bind=engine)
    now = datetime(2026, 6, 20)
    rows = [
        Technique(technique_id="T1190", name="Exploit Public-Facing Application"),
        CVE(cve_id="CVE-2026-0001", description="x", cvss_score=9.8, severity="CRITICAL",
            published_date=now),
        CorrelationResult(technique_id="T1190", cve_id="CVE-2026-0001", confidence_score=0.7,
                          confidence_level="HIGH", tactic="Initial Access", matched_keywords="x"),
        RiskScore(cve_id="CVE-2026-0001", risk_score=88.0, risk_level="CRITICAL",
                  model_version="t", generated_at=now),
        EPSSScore(cve_id="CVE-2026-0001", epss_score=0.7, percentile=0.99, updated_at=now,
                  collected_at=now),
        KEVEntry(cve_id="CVE-2026-0001", vendor_project="v", product="p", vulnerability_name="n",
                 date_added="2026-05-01", known_ransomware=False, updated_at=now, collected_at=now),
        PriorityScore(cve_id="CVE-2026-0001", priority_score=95.0, priority_level="CRITICAL",
                      kev_flag=True, epss_score=0.7, generated_at=now),
        ThreatActor(id=1, actor_name="APT-Z", source="misp-galaxy"),
        CTIRelationship(source_type="actor", source_key="APT-Z", relationship="exploits_cve",
                        target_type="cve", target_key="CVE-2026-0001", confidence=0.8, method="misp"),
        GraphMetric(entity_type="CVE", entity_id="CVE-2026-0001", degree_centrality=7,
                    pagerank=1.5, betweenness=10.0, community_id=1, node_similarity_score=0.0,
                    calculated_at=now),
        GraphMetric(entity_type="ThreatActor", entity_id="1", degree_centrality=80,
                    pagerank=40.0, betweenness=200.0, community_id=1, node_similarity_score=0.0,
                    calculated_at=now),
        WazuhAlert(id=1, wazuh_alert_id="a1", timestamp=now, agent_id="1", rule_id="100",
                   rule_level=12, description="sqli", mitre_techniques=["T1190"]),
        WazuhAlertEnrichment(alert_id=1, technique_id="T1190", cve_id="CVE-2026-0001",
                             threat_actor_id=1, kev_present=True, priority_score=96.0,
                             priority_level="CRITICAL", confidence_score=0.8,
                             evidence={"techniques": ["T1190"], "threat_actors": ["APT-Z"],
                                       "campaigns": [], "rationale": "KEV + actor"},
                             created_at=now),
    ]
    with TestingSessionLocal() as db:
        db.add_all(rows)
        db.commit()
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


# ── Provider abstraction ────────────────────────────────────

def test_provider_none_by_default():
    # AI_PROVIDER defaults to "none" -> deterministic fallback.
    assert get_provider() is None


# ── Query router: classification + entity extraction ────────

def test_router_extracts_cve_and_routes_risk():
    with TestingSessionLocal() as db:
        r = query_router.route("Why is CVE-2026-0001 high risk?", db)
    assert r.intent == "cve_risk"
    assert r.entities["cve_id"] == "CVE-2026-0001"


def test_router_resolves_actor_name():
    with TestingSessionLocal() as db:
        r = query_router.route("Show attack paths related to APT-Z", db)
    assert r.intent == "attack_paths_actor"
    assert r.entities["actor_id"] == 1


def test_router_intents_for_sample_questions():
    cases = {
        "Which actors are associated with KEV vulnerabilities?": "kev_actors",
        "Which alerts should analysts investigate first?": "triage_alerts",
        "What are the most dangerous CVEs in my environment?": "dangerous_cves",
        "Which MITRE techniques are most frequently observed?": "top_techniques",
    }
    with TestingSessionLocal() as db:
        for q, intent in cases.items():
            assert query_router.route(q, db).intent == intent, q


def test_router_followup_uses_context():
    with TestingSessionLocal() as db:
        r = query_router.route("show me more about that actor", db,
                               context={"last_entities": {"actor_id": 1, "actor_name": "APT-Z"}})
    assert r.resolved_from_context is True
    assert r.entities["actor_id"] == 1


# ── Cypher safety controls (13.5) ───────────────────────────

def test_only_registered_templates_run():
    with pytest.raises(ValueError):
        query_router.run_template("DROP_EVERYTHING", {})


def test_write_cypher_rejected():
    assert query_router.is_safe_cypher("MATCH (n) RETURN n") is True
    assert query_router.is_safe_cypher("MATCH (n) DETACH DELETE n") is False
    assert query_router.is_safe_cypher("MERGE (n:X) RETURN n") is False


# ── Evidence engine (grounded, no LLM) ──────────────────────

def test_cve_risk_evidence_grounded():
    from backend.app.ai import investigation_engine
    with TestingSessionLocal() as db:
        ev = investigation_engine.gather_evidence("cve_risk", {"cve_id": "CVE-2026-0001"}, db)
    f = ev["findings"]
    assert f["in_kev"] is True
    assert f["ml_risk_score"] == 88.0
    assert "T1190" in f["techniques"]
    assert "APT-Z" in f["threat_actors"]
    assert ev["confidence"] > 0.5
    assert "CVE-2026-0001" in ev["risk_justification"]


# ── API ─────────────────────────────────────────────────────

def test_ai_query_endpoint():
    r = client.post("/ai/query", json={"question": "Why is CVE-2026-0001 high risk?"})
    assert r.status_code == 200
    body = r.json()
    assert body["intent"] == "cve_risk"
    assert body["generator"] == "deterministic"
    assert body["findings"]["in_kev"] is True
    assert body["data_sources"]


def test_ai_query_empty_rejected():
    assert client.post("/ai/query", json={"question": "   "}).status_code == 400


def test_ai_investigate_cve():
    r = client.post("/ai/investigate/cve", json={"cve_id": "CVE-2026-0001"})
    assert r.status_code == 200
    assert r.json()["intent"] == "cve_risk"


def test_ai_investigate_alert():
    r = client.post("/ai/investigate/alert", json={"alert_id": 1})
    assert r.status_code == 200
    assert r.json()["intent"] == "alert_investigation"


def test_ai_chat_multiturn_memory():
    sid = "test-session-1"
    r1 = client.post("/ai/chat", json={"message": "Tell me about APT-Z", "session_id": sid})
    assert r1.status_code == 200
    assert r1.json()["entities"].get("actor_id") == 1
    # Follow-up with a pronoun should resolve to the same actor from memory.
    r2 = client.post("/ai/chat", json={"message": "show me more about that actor", "session_id": sid})
    assert r2.json()["resolved_from_context"] is True
    assert r2.json()["entities"].get("actor_id") == 1
