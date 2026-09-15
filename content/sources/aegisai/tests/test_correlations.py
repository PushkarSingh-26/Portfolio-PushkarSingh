"""Tests for the correlation engine and /correlations endpoints.

Endpoint tests use an in-memory SQLite database seeded with a few techniques,
CVEs, and engine-generated correlations, via a get_db dependency override -
no PostgreSQL container or network needed.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.correlation.engine import (
    combine_weights,
    confidence_level,
    correlate_description,
    run_correlation,
)
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models import CVE, CorrelationResult, Technique

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def seed_database():
    Base.metadata.create_all(
        bind=engine,
        tables=[Technique.__table__, CVE.__table__, CorrelationResult.__table__],
    )
    techniques = [
        Technique(technique_id="T1190", name="Exploit Public-Facing Application"),
        Technique(technique_id="T1059", name="Command and Scripting Interpreter"),
        Technique(technique_id="T1068", name="Exploitation for Privilege Escalation"),
        Technique(technique_id="T1486", name="Data Encrypted for Impact"),
    ]
    cves = [
        CVE(
            cve_id="CVE-2024-1000",
            description="A SQL injection vulnerability allows remote attackers "
            "to execute arbitrary commands and gain elevated privileges.",
            cvss_score=9.8,
            severity="CRITICAL",
            published_date=datetime(2024, 1, 1),
        ),
        CVE(
            cve_id="CVE-2024-2000",
            description="A cross-site scripting (XSS) issue in the web console.",
            cvss_score=6.1,
            severity="MEDIUM",
            published_date=datetime(2024, 2, 1),
        ),
        CVE(
            cve_id="CVE-2024-3000",
            description="Ransomware can encrypt files after exploitation.",
            cvss_score=8.0,
            severity="HIGH",
            published_date=datetime(2024, 3, 1),
        ),
        CVE(
            cve_id="CVE-2024-4000",
            description="A minor cosmetic UI glitch with no security impact.",
            cvss_score=2.0,
            severity="LOW",
            published_date=datetime(2024, 4, 1),
        ),
    ]
    with TestingSessionLocal() as db:
        db.add_all(techniques + cves)
        db.commit()
        valid = {"T1190", "T1059", "T1068", "T1486"}
        run_correlation(db, valid_technique_ids=valid)

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


# ── Engine unit tests ───────────────────────────────────────

def test_combine_weights_noisy_or():
    assert combine_weights([0.7]) == 0.7
    # 1 - (1-0.7)(1-0.5) = 1 - 0.15 = 0.85
    assert combine_weights([0.7, 0.5]) == 0.85


def test_confidence_level_buckets():
    assert confidence_level(0.85) == "HIGH"
    assert confidence_level(0.5) == "MEDIUM"
    assert confidence_level(0.3) == "LOW"


def test_correlate_description_matches_sqli():
    matches = correlate_description("SQL injection allows remote code execution")
    techniques = {m["technique_id"] for m in matches}
    assert "T1190" in techniques  # sql injection
    assert "T1203" in techniques  # remote code execution


def test_correlate_description_word_boundary():
    # "dos" must not match inside "Windows".
    matches = correlate_description("An issue affecting Windows endpoints.")
    assert all(m["technique_id"] != "T1499" for m in matches)


def test_no_match_for_benign_text():
    assert correlate_description("A minor cosmetic UI glitch.") == []


# ── API tests ───────────────────────────────────────────────

def test_list_correlations_ordered_by_confidence():
    resp = client.get("/correlations")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) > 0
    scores = [c["confidence_score"] for c in body]
    assert scores == sorted(scores, reverse=True)
    # Responses are enriched with technique name + CVE severity.
    assert body[0]["technique_name"]
    assert "matched_keywords" in body[0]


def test_filter_by_confidence_level():
    resp = client.get("/correlations?confidence_level=HIGH")
    assert resp.status_code == 200
    assert all(c["confidence_level"] == "HIGH" for c in resp.json())


def test_invalid_confidence_level_rejected():
    assert client.get("/correlations?confidence_level=SUPER").status_code == 400


def test_filter_by_min_confidence():
    resp = client.get("/correlations?min_confidence=0.8")
    assert resp.status_code == 200
    assert all(c["confidence_score"] >= 0.8 for c in resp.json())


def test_filter_by_severity():
    resp = client.get("/correlations?severity=CRITICAL")
    assert resp.status_code == 200
    assert all(c["severity"] == "CRITICAL" for c in resp.json())


def test_correlations_for_technique():
    resp = client.get("/correlations/T1190")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) >= 1
    assert all(c["technique_id"] == "T1190" for c in body)


def test_correlations_for_technique_not_found():
    assert client.get("/correlations/T9999").status_code == 404


def test_correlations_for_cve():
    resp = client.get("/correlations/cve/CVE-2024-1000")
    assert resp.status_code == 200
    body = resp.json()
    techniques = {c["technique_id"] for c in body}
    # This CVE mentions SQLi, arbitrary commands, and privilege escalation.
    assert {"T1190", "T1059", "T1068"} <= techniques


def test_correlations_for_cve_not_found():
    assert client.get("/correlations/cve/CVE-0000-0000").status_code == 404


def test_correlation_stats():
    resp = client.get("/stats/correlations")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["total_correlations"] >= 1
    assert stats["critical_cves_mapped"] >= 1
    assert isinstance(stats["most_associated_techniques"], list)
    assert isinstance(stats["most_correlated_cves"], list)
    assert set(stats["by_confidence_level"]).issubset({"LOW", "MEDIUM", "HIGH"})
