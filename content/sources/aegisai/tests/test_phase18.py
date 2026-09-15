"""Tests for Phase 18 — orchestration, scheduling, retry, ticketing, APIs.

Executor/history tests use an in-memory SQLite DB with jobs monkeypatched, so no
real components run. Scheduler/ticketing are tested without external services.
All deterministic; no network required.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.orchestration import executor, history, jobs, scheduler
from backend.app.orchestration.jobs import JOB_REGISTRY

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup():
    import backend.app.database as dbmod
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = _override_get_db
    # executor uses backend.app.database.SessionLocal directly -> point it at the
    # test DB for the duration, then RESTORE so other test modules are unaffected.
    _orig_session = dbmod.SessionLocal
    dbmod.SessionLocal = TestingSessionLocal
    try:
        yield
    finally:
        dbmod.SessionLocal = _orig_session
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)


client = TestClient(app)


# ── Scheduler / registry ────────────────────────────────────

def test_registry_has_production_jobs():
    expected = {"wazuh_sync", "misp_sync", "epss_sync", "kev_sync", "nvd_sync", "mitre_sync",
                "correlation", "graph_sync", "graph_analytics", "embeddings", "link_prediction",
                "coverage", "risk_scoring", "autonomous_triage", "daily_briefing", "weekly_cti"}
    assert expected <= set(JOB_REGISTRY)


def test_scheduled_jobs_have_schedules():
    js = scheduler.scheduled_jobs()
    assert len(js) == len(JOB_REGISTRY)
    assert all(j["schedule"] for j in js)


def test_build_scheduler_creates_all_jobs():
    # build_scheduler() constructs but does NOT start; get_jobs works unstarted.
    sched = scheduler.build_scheduler()
    assert len(sched.get_jobs()) == len(JOB_REGISTRY)


# ── Executor: success, retry, history ───────────────────────

def test_executor_success_records_run(monkeypatch):
    monkeypatch.setitem(JOB_REGISTRY, "correlation",
                        (lambda: {"records_processed": 7, "metadata": {"ok": True}},
                         "analytics", "test", {"hour": 1}))
    run = executor.run_job("correlation")
    assert run["status"] == "completed"
    assert run["records_processed"] == 7


def test_executor_retries_then_fails(monkeypatch):
    calls = {"n": 0}

    def _boom():
        calls["n"] += 1
        raise RuntimeError("boom")

    monkeypatch.setitem(JOB_REGISTRY, "coverage", (_boom, "analytics", "t", {"hour": 1}))
    run = executor.run_job("coverage", max_retries=2)
    assert run["status"] == "failed"
    assert "boom" in run["error_message"]
    assert calls["n"] == 3  # 1 try + 2 retries


def test_executor_unknown_job():
    with pytest.raises(ValueError):
        executor.run_job("does_not_exist")


def test_history_and_stats():
    with TestingSessionLocal() as db:
        runs = history.recent_runs(db, limit=10)
        stats = history.job_stats(db)
    assert len(runs) >= 1
    assert isinstance(stats, dict)


# ── Pipeline ────────────────────────────────────────────────

def test_pipeline_runs_in_order(monkeypatch):
    seen = []

    def _mk(name):
        def _fn():
            seen.append(name)
            return {"records_processed": 1, "metadata": {}}
        return _fn

    for n in ("correlation", "risk_scoring", "graph_sync"):
        monkeypatch.setitem(JOB_REGISTRY, n, (_mk(n), "test", "t", {"hour": 1}))
    from backend.app.orchestration import pipeline
    res = pipeline.run_pipeline(steps=["correlation", "risk_scoring", "graph_sync"])
    assert res["succeeded"] == 3
    assert seen == ["correlation", "risk_scoring", "graph_sync"]


# ── Ticketing providers ─────────────────────────────────────

def test_ticket_mock_default():
    from backend.app.ticketing import create_ticket, get_provider
    assert get_provider().name == "mock"
    t = create_ticket("Critical alert", "body", "CRITICAL")
    assert t["provider"] == "mock" and t["ticket_id"].startswith("MOCK-")


def test_export_investigation_mock():
    from backend.app.ticketing import export_investigation
    out = export_investigation({"target": "alert:1", "investigation_id": 1,
                                "report": {"risk_assessment": {"level": "CRITICAL"},
                                           "executive_summary": "summary"}})
    assert out["provider"] == "mock"


def test_shuffle_provider_requires_config():
    from backend.app.ticketing.providers import ShuffleProvider
    with pytest.raises(RuntimeError):
        ShuffleProvider().create_ticket("t", "b", "HIGH")


# ── APIs ────────────────────────────────────────────────────

def test_api_jobs():
    r = client.get("/pipeline/jobs")
    assert r.status_code == 200
    assert len(r.json()["jobs"]) == len(JOB_REGISTRY)


def test_api_run_single(monkeypatch):
    monkeypatch.setitem(JOB_REGISTRY, "coverage",
                        (lambda: {"records_processed": 3, "metadata": {}}, "analytics", "t", {"hour": 1}))
    r = client.post("/pipeline/run/coverage")
    assert r.status_code == 200 and r.json()["status"] == "completed"


def test_api_run_unknown_job_400():
    assert client.post("/pipeline/run/nope").status_code == 400


def test_api_health_and_history():
    assert client.get("/pipeline/health").status_code == 200
    assert client.get("/pipeline/history").status_code == 200
    assert client.get("/pipeline/status").status_code == 200
