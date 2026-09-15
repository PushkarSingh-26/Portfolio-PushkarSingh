"""Tests for Phase 14 — Agentic SOC Analyst.

In-memory SQLite seeded with CTI + graph + Wazuh data. The agent runs over real
tools deterministically; graph-dependent tools degrade gracefully without Neo4j.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.agents import agent, blast_radius, memory, planner
from backend.app.agents.tools import TOOL_REGISTRY, run_tool
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
        CVE(cve_id="CVE-2026-0001", description="rce", cvss_score=9.8, severity="CRITICAL",
            published_date=now),
        CorrelationResult(technique_id="T1190", cve_id="CVE-2026-0001", confidence_score=0.7,
                          confidence_level="HIGH", tactic="Initial Access", matched_keywords="rce"),
        RiskScore(cve_id="CVE-2026-0001", risk_score=88.0, risk_level="CRITICAL",
                  model_version="v5", generated_at=now),
        EPSSScore(cve_id="CVE-2026-0001", epss_score=0.8, percentile=0.99, updated_at=now, collected_at=now),
        KEVEntry(cve_id="CVE-2026-0001", vendor_project="v", product="p", vulnerability_name="n",
                 date_added="2026-05-01", due_date="2026-06-15", known_ransomware=False,
                 updated_at=now, collected_at=now),
        PriorityScore(cve_id="CVE-2026-0001", priority_score=95.0, priority_level="CRITICAL",
                      kev_flag=True, epss_score=0.8, generated_at=now),
        ThreatActor(id=1, actor_name="APT-X", source="misp-galaxy"),
        CTIRelationship(source_type="actor", source_key="APT-X", relationship="exploits_cve",
                        target_type="cve", target_key="CVE-2026-0001", confidence=0.8, method="misp"),
        GraphMetric(entity_type="CVE", entity_id="CVE-2026-0001", degree_centrality=7, pagerank=1.8,
                    betweenness=10.0, community_id=3, node_similarity_score=0.0, calculated_at=now),
        WazuhAlert(id=1, wazuh_alert_id="a1", timestamp=now, agent_id="1", rule_id="100",
                   rule_level=12, description="sqli", mitre_techniques=["T1190"]),
        WazuhAlertEnrichment(alert_id=1, technique_id="T1190", cve_id="CVE-2026-0001",
                             threat_actor_id=1, kev_present=True, priority_score=95.0,
                             priority_level="CRITICAL", confidence_score=0.8,
                             evidence={"techniques": ["T1190"], "threat_actors": ["APT-X"],
                                       "cves": [{"cve_id": "CVE-2026-0001"}], "campaigns": [],
                                       "rationale": "KEV + actor"}),
    ]
    with TestingSessionLocal() as db:
        db.add_all(rows)
        db.commit()
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


# ── Planner ─────────────────────────────────────────────────

def test_plan_alert_is_ordered_and_explainable():
    p = planner.plan("alert", {"alert_id": 1})
    assert [s["step"] for s in p] == list(range(1, len(p) + 1))
    assert all(s["rationale"] for s in p)
    assert p[0]["tool"] == "wazuh_alert_retrieval"


def test_plan_unknown_type_raises():
    with pytest.raises(ValueError):
        planner.plan("bogus", {})


# ── Tools ───────────────────────────────────────────────────

def test_tool_registry_and_run():
    assert "risk_score_retrieval" in TOOL_REGISTRY
    with TestingSessionLocal() as db:
        r = run_tool("risk_score_retrieval", db, {"cve_id": "CVE-2026-0001"})
    assert r["ok"] is True
    assert r["data"]["risk_score"] == 88.0


def test_run_tool_unknown_raises():
    with TestingSessionLocal() as db:
        with pytest.raises(ValueError):
            run_tool("rm_rf", db, {})


def test_kev_tool():
    with TestingSessionLocal() as db:
        r = run_tool("kev_retrieval", db, {"cve_id": "CVE-2026-0001"})
    assert r["data"]["in_kev"] is True


# ── Blast radius (community path is DB-only) ────────────────

def test_blast_radius_community_from_cache():
    with TestingSessionLocal() as db:
        br = blast_radius.compute("community", 3, db)
    assert br["seed"]["type"] == "community"
    assert "CVE-2026-0001" in br["affected"]["affected_cves"]
    assert br["total_affected"] >= 1


# ── Agent end-to-end (deterministic) ────────────────────────

def test_agent_investigate_alert_full():
    with TestingSessionLocal() as db:
        r = agent.investigate_alert(db, 1)
    assert r["investigation_id"]
    assert len(r["plan"]) == 8
    assert any(c["status"] == "ok" for c in r["tool_calls"])
    rep = r["report"]
    assert rep["risk_assessment"]["level"] in ("CRITICAL", "HIGH")
    # KEV present -> "Patch immediately" recommendation is evidence-cited
    actions = [x["action"] for x in rep["recommendations"]]
    assert "Patch immediately" in actions
    assert all(x["evidence"] for x in rep["recommendations"])
    assert rep["confidence_score"] > 0


def test_agent_investigate_cve_and_persist():
    with TestingSessionLocal() as db:
        r = agent.investigate_cve(db, "CVE-2026-0001")
        inv = memory.get(db, r["investigation_id"])
    assert inv is not None
    assert inv.investigation_type == "cve"
    assert inv.report["risk_assessment"]["level"] in ("CRITICAL", "HIGH")


def test_agent_lineage():
    with TestingSessionLocal() as db:
        r1 = agent.investigate_cve(db, "CVE-2026-0001")
        r2 = agent.investigate_cve(db, "CVE-2026-0001", parent_id=r1["investigation_id"])
        chain = memory.lineage(db, r2["investigation_id"])
    assert [c.id for c in chain] == [r2["investigation_id"], r1["investigation_id"]]


# ── APIs ────────────────────────────────────────────────────

def test_api_investigate_alert():
    r = client.post("/agent/investigate/alert", json={"alert_id": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["report"]["recommendations"]
    assert body["confidence"] > 0


def test_api_investigate_invalid_type():
    r = client.post("/agent/investigate", json={"investigation_type": "nope", "target": {}})
    assert r.status_code == 400


def test_api_blast_radius():
    r = client.post("/agent/blast-radius", json={"entity_type": "community", "entity_id": "3"})
    assert r.status_code == 200
    assert r.json()["total_affected"] >= 1


def test_api_history_and_report():
    client.post("/agent/investigate/cve", json={"cve_id": "CVE-2026-0001"})
    h = client.get("/agent/history")
    assert h.status_code == 200 and len(h.json()) >= 1
    inv_id = h.json()[0]["id"]
    rep = client.post("/agent/report", json={"investigation_id": inv_id})
    assert rep.status_code == 200
    assert "report" in rep.json()


def test_api_report_404():
    assert client.post("/agent/report", json={"investigation_id": 999999}).status_code == 404


def test_api_tasks_lists_tools():
    r = client.get("/agent/tasks")
    assert r.status_code == 200
    assert any(t["name"] == "risk_score_retrieval" for t in r.json()["tools"])
