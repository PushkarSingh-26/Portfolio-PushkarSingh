"""Job registry (Phase 18.1).

Each job wraps an EXISTING component entrypoint and returns
{"records_processed": int, "metadata": dict}. Internal analytics jobs run
in-process (idempotent upserts); external collectors run as subprocesses
(`python -m collectors.*`) so they stay decoupled and restart-safe.
"""

import logging
import subprocess
import sys

log = logging.getLogger("orchestration.jobs")

COLLECTOR_TIMEOUT = 600


def _run_collector(module: str, args: list[str] | None = None) -> dict:
    """Run a collector as a subprocess; parse a best-effort processed count."""
    cmd = [sys.executable, "-m", module, *(args or [])]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=COLLECTOR_TIMEOUT)
    tail = (proc.stdout or "")[-500:] + (proc.stderr or "")[-300:]
    if proc.returncode != 0:
        raise RuntimeError(f"{module} exited {proc.returncode}: {tail[-300:]}")
    processed = 0
    for token in ("inserted", "Inserted", "Scored", "Ingested", "persisted"):
        if token.lower() in tail.lower():
            import re
            m = re.search(rf"{token}[:\s]+(\d+)", tail)
            if m:
                processed = max(processed, int(m.group(1)))
    return {"records_processed": processed, "metadata": {"module": module, "output_tail": tail[-300:]}}


# ── internal (in-process) jobs ──────────────────────────────

def _correlation():
    from backend.app.correlation.engine import run_correlation
    from backend.app.database import SessionLocal
    with SessionLocal() as db:
        s = run_correlation(db)
    return {"records_processed": s.get("total_correlations", 0), "metadata": s}


def _risk_scoring():
    from backend.app.database import SessionLocal
    from ml.inference import score_all
    with SessionLocal() as db:
        s = score_all(db)
    return {"records_processed": s.get("scored", 0), "metadata": {k: v for k, v in s.items()
            if k in ("scored", "model_version", "level_distribution")}}


def _graph_sync():
    from backend.app.graph.graph_sync import run_sync
    s = run_sync()
    return {"records_processed": s.get("total_nodes", 0), "metadata": s}


def _graph_analytics():
    from backend.app.database import SessionLocal
    from backend.app.graph.analytics import run_analytics
    with SessionLocal() as db:
        s = run_analytics(db)
    return {"records_processed": s.get("persisted_metrics", 0), "metadata": s}


def _graph_intelligence():
    from backend.app.database import SessionLocal
    from backend.app.graph.intelligence import run_intelligence
    with SessionLocal() as db:
        s = run_intelligence(db)
    return {"records_processed": s.get("insights_generated", 0), "metadata": s}


def _embeddings():
    from backend.app.predictions.embeddings import compute_embeddings
    n = compute_embeddings("fastrp")
    return {"records_processed": n, "metadata": {"model": "fastrp", "nodes": n}}


def _link_prediction():
    from backend.app.database import SessionLocal
    from backend.app.predictions.link_prediction import run
    with SessionLocal() as db:
        s = run(db)
    return {"records_processed": s.get("predictions", 0), "metadata": s}


def _coverage():
    from backend.app.coverage.engine import run_coverage
    from backend.app.database import SessionLocal
    with SessionLocal() as db:
        s = run_coverage(db)
    return {"records_processed": s.get("observed", 0),
            "metadata": {"coverage_pct": s.get("coverage_pct"), "observed": s.get("observed"),
                         "total": s.get("techniques_total")}}


def _attack_paths():
    from backend.app.database import SessionLocal
    from backend.app.graph.attack_paths import analyze_and_store
    with SessionLocal() as db:
        s = analyze_and_store(db)
    return {"records_processed": s.get("total_paths", 0), "metadata": s}


def _autonomous_triage():
    from backend.app.database import SessionLocal
    from backend.app.orchestration.rules import apply_investigation_rules
    with SessionLocal() as db:
        s = apply_investigation_rules(db)
    return {"records_processed": s.get("investigated", 0), "metadata": s}


def _daily_briefing():
    from backend.app.database import SessionLocal
    from backend.app.reporting.briefings import daily_briefing
    with SessionLocal() as db:
        s = daily_briefing(db)
    return {"records_processed": 1, "metadata": {"report_id": s["report_id"]}}


def _weekly_cti():
    from backend.app.database import SessionLocal
    from backend.app.reporting.briefings import weekly_cti
    with SessionLocal() as db:
        s = weekly_cti(db)
    return {"records_processed": 1, "metadata": {"report_id": s["report_id"]}}


# job_name -> (callable, job_type, description, cron)
JOB_REGISTRY = {
    "wazuh_sync": (lambda: _run_collector("collectors.wazuh"), "collector", "Wazuh agents+alerts", {"minute": "*/15"}),
    "misp_sync": (lambda: _run_collector("collectors.misp"), "collector", "MISP intel", {"minute": "*/30"}),
    "epss_sync": (lambda: _run_collector("collectors.epss"), "collector", "EPSS scores", {"hour": 1, "minute": 0}),
    "kev_sync": (lambda: _run_collector("collectors.cisa_kev"), "collector", "CISA KEV", {"hour": 1, "minute": 15}),
    "nvd_sync": (lambda: _run_collector("collectors.nvd_cve"), "collector", "NVD CVEs", {"hour": 2, "minute": 0}),
    "mitre_sync": (lambda: _run_collector("collectors.mitre_attack"), "collector", "MITRE ATT&CK", {"day_of_week": "sun", "hour": 3}),
    "correlation": (_correlation, "analytics", "ATT&CK<->CVE correlation", {"hour": 3, "minute": 15}),
    "graph_sync": (_graph_sync, "graph", "PostgreSQL->Neo4j sync", {"hour": 3, "minute": 30}),
    "graph_analytics": (_graph_analytics, "graph", "GDS centrality/communities", {"hour": 4, "minute": 0}),
    "graph_intelligence": (_graph_intelligence, "graph", "Graph insights", {"hour": 4, "minute": 15}),
    "embeddings": (_embeddings, "graph", "FastRP embeddings", {"hour": 4, "minute": 30}),
    "link_prediction": (_link_prediction, "ml", "Link prediction", {"hour": 5, "minute": 0}),
    "coverage": (_coverage, "analytics", "ATT&CK coverage", {"hour": 5, "minute": 30}),
    "attack_paths": (_attack_paths, "graph", "Attack-path metadata", {"hour": 5, "minute": 45}),
    "risk_scoring": (_risk_scoring, "ml", "ML Risk Scoring V6", {"hour": 6, "minute": 0}),
    "autonomous_triage": (_autonomous_triage, "soc", "Autonomous investigation rules", {"hour": 6, "minute": 30}),
    "daily_briefing": (_daily_briefing, "reporting", "SOC daily briefing", {"hour": 8, "minute": 0}),
    "weekly_cti": (_weekly_cti, "reporting", "Executive CTI report", {"day_of_week": "mon", "hour": 9}),
}

# Dependency-ordered internal pipeline (collectors optional/external).
PIPELINE_ORDER = [
    "correlation", "risk_scoring", "graph_sync", "graph_analytics", "graph_intelligence",
    "embeddings", "link_prediction", "coverage", "attack_paths", "autonomous_triage",
    "daily_briefing",
]
COLLECTOR_JOBS = ["wazuh_sync", "misp_sync", "epss_sync", "kev_sync", "nvd_sync", "mitre_sync"]


def get_job(name: str):
    if name not in JOB_REGISTRY:
        raise ValueError(f"Unknown job '{name}'")
    return JOB_REGISTRY[name]
