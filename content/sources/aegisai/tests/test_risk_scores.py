"""Tests for the ML risk-scoring pipeline and /risk-scores + /stats/techniques.

Uses an in-memory SQLite database seeded with techniques, CVEs, correlations,
and risk scores, shared between the API (via dependency override) and direct
calls into the ML modules. No PostgreSQL container required.
"""

from datetime import datetime, timedelta

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models import CVE, CorrelationResult, RiskScore, Technique
from ml.feature_engineering import (
    FEATURE_COLUMNS,
    build_features,
    compute_weak_labels,
)
from ml.risk_model import risk_level

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
    Base.metadata.create_all(bind=engine)
    now = datetime(2026, 6, 1)
    techniques = [
        Technique(technique_id="T1190", name="Exploit Public-Facing Application"),
        Technique(technique_id="T1059", name="Command and Scripting Interpreter"),
        Technique(technique_id="T1486", name="Data Encrypted for Impact"),
    ]
    cves = [
        CVE(cve_id="CVE-2026-0001", description="x" * 200, cvss_score=9.8,
            severity="CRITICAL", published_date=now - timedelta(days=5)),
        CVE(cve_id="CVE-2026-0002", description="y" * 100, cvss_score=5.0,
            severity="MEDIUM", published_date=now - timedelta(days=100)),
        # Missing CVSS -> exercises imputation from severity.
        CVE(cve_id="CVE-2026-0003", description="z" * 50, cvss_score=None,
            severity="HIGH", published_date=now - timedelta(days=30)),
        # Uncorrelated CVE -> must NOT appear in features.
        CVE(cve_id="CVE-2026-9999", description="benign", cvss_score=1.0,
            severity="LOW", published_date=now),
    ]
    correlations = [
        CorrelationResult(technique_id="T1190", cve_id="CVE-2026-0001",
                          confidence_score=0.7, confidence_level="HIGH",
                          tactic="Initial Access", matched_keywords="sql injection"),
        CorrelationResult(technique_id="T1059", cve_id="CVE-2026-0001",
                          confidence_score=0.7, confidence_level="HIGH",
                          tactic="Execution", matched_keywords="command injection"),
        CorrelationResult(technique_id="T1486", cve_id="CVE-2026-0002",
                          confidence_score=0.5, confidence_level="MEDIUM",
                          tactic="Impact", matched_keywords="ransomware"),
        CorrelationResult(technique_id="T1190", cve_id="CVE-2026-0003",
                          confidence_score=0.4, confidence_level="MEDIUM",
                          tactic="Initial Access", matched_keywords="ssrf"),
    ]
    risk_scores = [
        RiskScore(cve_id="CVE-2026-0001", risk_score=88.0, risk_level="CRITICAL",
                  model_version="risk-test-v1", generated_at=now),
        RiskScore(cve_id="CVE-2026-0002", risk_score=45.0, risk_level="MEDIUM",
                  model_version="risk-test-v1", generated_at=now),
        RiskScore(cve_id="CVE-2026-0003", risk_score=63.0, risk_level="HIGH",
                  model_version="risk-test-v1", generated_at=now),
    ]
    with TestingSessionLocal() as db:
        db.add_all(techniques + cves + correlations + risk_scores)
        db.commit()

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


# ── Feature engineering ─────────────────────────────────────

def test_build_features_shape_and_columns():
    with TestingSessionLocal() as db:
        df = build_features(db, reference_time=datetime(2026, 6, 1))
    assert list(df.columns) == FEATURE_COLUMNS
    # Only correlated CVEs are featurized.
    assert set(df.index) == {"CVE-2026-0001", "CVE-2026-0002", "CVE-2026-0003"}
    assert "CVE-2026-9999" not in df.index


def test_build_features_imputes_missing_cvss():
    with TestingSessionLocal() as db:
        df = build_features(db, reference_time=datetime(2026, 6, 1))
    # CVE-2026-0003 had no CVSS; HIGH severity proxy is 7.5.
    assert df.loc["CVE-2026-0003", "cvss_score"] == 7.5
    assert df["cvss_score"].notna().all()


def test_build_features_counts():
    with TestingSessionLocal() as db:
        df = build_features(db, reference_time=datetime(2026, 6, 1))
    # CVE-0001 maps to two techniques across two tactics.
    assert df.loc["CVE-2026-0001", "num_mappings"] == 2
    assert df.loc["CVE-2026-0001", "distinct_tactics"] == 2
    assert df.loc["CVE-2026-0001", "is_critical"] == 1


# ── Weak labels & levels ────────────────────────────────────

def test_weak_labels_in_range_and_monotonic():
    df = pd.DataFrame(
        {
            "cvss_score": [9.8, 3.0],
            "max_confidence": [0.8, 0.4],
            "num_mappings": [3, 1],
            "technique_popularity": [1.0, 0.1],
            "published_age_days": [5, 5],
            "is_critical": [1, 0],
            "is_high_confidence": [1, 0],
        }
    )
    labels = compute_weak_labels(df)
    assert (labels >= 0).all() and (labels <= 100).all()
    # The severe row must score higher than the mild row.
    assert labels.iloc[0] > labels.iloc[1]


def test_risk_level_thresholds():
    assert risk_level(90) == "CRITICAL"
    assert risk_level(60) == "HIGH"
    assert risk_level(30) == "MEDIUM"
    assert risk_level(10) == "LOW"


# ── Model training & explainability (real estimator) ────────

def test_model_trains_and_predicts_in_range():
    from ml.risk_model import build_model

    with TestingSessionLocal() as db:
        df = build_features(db, reference_time=datetime(2026, 6, 1))
    labels = compute_weak_labels(df)
    model, algorithm = build_model()
    model.fit(df[FEATURE_COLUMNS], labels)
    preds = model.predict(df[FEATURE_COLUMNS])
    assert len(preds) == len(df)
    assert algorithm in {"xgboost", "random_forest"}
    assert hasattr(model, "feature_importances_")


def test_explainability_global_importance():
    from ml.explainability import explain_instance, global_importance
    from ml.risk_model import build_model

    with TestingSessionLocal() as db:
        df = build_features(db, reference_time=datetime(2026, 6, 1))
    labels = compute_weak_labels(df)
    model, _ = build_model()
    model.fit(df[FEATURE_COLUMNS], labels)

    ranking = global_importance(model)
    assert len(ranking) == len(FEATURE_COLUMNS)
    assert ranking == sorted(ranking, key=lambda d: d["importance"], reverse=True)

    contributions = explain_instance(model, df.iloc[0], df)
    assert len(contributions) == len(FEATURE_COLUMNS)


# ── API: risk scores ────────────────────────────────────────

def test_list_risk_scores_ordered():
    resp = client.get("/risk-scores")
    assert resp.status_code == 200
    scores = [r["risk_score"] for r in resp.json()]
    assert scores == sorted(scores, reverse=True)
    assert resp.json()[0]["severity"]  # enriched with CVE context


def test_filter_by_risk_level():
    resp = client.get("/risk-scores?risk_level=CRITICAL")
    assert resp.status_code == 200
    assert all(r["risk_level"] == "CRITICAL" for r in resp.json())


def test_invalid_risk_level_rejected():
    assert client.get("/risk-scores?risk_level=EXTREME").status_code == 400


def test_min_score_filter():
    resp = client.get("/risk-scores?min_score=60")
    assert resp.status_code == 200
    assert all(r["risk_score"] >= 60 for r in resp.json())


def test_top_risk_scores():
    resp = client.get("/risk-scores/top?limit=2")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert body[0]["cve_id"] == "CVE-2026-0001"


def test_get_risk_score_by_cve():
    resp = client.get("/risk-scores/CVE-2026-0001")
    assert resp.status_code == 200
    assert resp.json()["risk_level"] == "CRITICAL"


def test_get_risk_score_not_found():
    assert client.get("/risk-scores/CVE-2026-9999").status_code == 404


def test_risk_score_stats():
    resp = client.get("/stats/risk-scores")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["total"] == 3
    assert stats["by_level"]["CRITICAL"] == 1
    assert stats["max_score"] == 88.0
    assert sum(stats["distribution"].values()) == 3


# ── API: technique stats ────────────────────────────────────

def test_technique_stats():
    resp = client.get("/stats/techniques")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["total"] == 3
    assert stats["parent_techniques"] + stats["sub_techniques"] == 3
