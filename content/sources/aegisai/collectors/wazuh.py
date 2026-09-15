"""Wazuh SOC connector (Phase 10).

Production path pulls agents from the Wazuh Manager API (JWT auth) and alerts
from the Wazuh Indexer (OpenSearch). All credentials come from environment
variables; nothing is hardcoded.

    python -m collectors.wazuh                       # full sync (agents + alerts)
    python -m collectors.wazuh --since 2026-06-01    # incremental alerts since
    python -m collectors.wazuh --sample collectors/fixtures/sample_wazuh.json  # offline

Environment variables:
    WAZUH_API_URL, WAZUH_USERNAME, WAZUH_PASSWORD     (manager API :55000)
    INDEXER_URL, INDEXER_USERNAME, INDEXER_PASSWORD   (indexer :9200)
    WAZUH_VERIFY_SSL                                  (true/false)

After ingestion the alert enrichment + SOC priority engine is run.
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime

import requests
import urllib3
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.database import SessionLocal

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [wazuh] %(message)s")
log = logging.getLogger("collectors.wazuh")

PAGE_SIZE = 500
MAX_RETRIES = 3
ALERTS_INDEX = "wazuh-alerts-*"


def _session(verify_ssl: bool) -> requests.Session:
    s = requests.Session()
    s.verify = verify_ssl
    if not verify_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    return s


def _retry(fn, *args, **kwargs):
    attempt = 0
    while True:
        try:
            return fn(*args, **kwargs)
        except requests.RequestException as exc:
            attempt += 1
            if attempt >= MAX_RETRIES:
                raise
            log.warning("request failed (attempt %d): %s", attempt, exc)
            time.sleep(2 * attempt)


# ────────────────────────── Manager API: agents ──────────────────────────

def get_api_token(session, settings) -> str:
    resp = _retry(
        session.post,
        f"{settings.wazuh_api_url.rstrip('/')}/security/user/authenticate",
        auth=(settings.wazuh_username, settings.wazuh_password),
        timeout=15,
    )
    resp.raise_for_status()
    token = resp.json().get("data", {}).get("token")
    if not token:
        raise RuntimeError("Wazuh API authentication returned no token")
    log.info("Authenticated to Wazuh Manager API")
    return token


def fetch_agents(session, settings, token: str) -> list[dict]:
    headers = {"Authorization": f"Bearer {token}"}
    agents, offset = [], 0
    while True:
        resp = _retry(
            session.get,
            f"{settings.wazuh_api_url.rstrip('/')}/agents",
            headers=headers, params={"offset": offset, "limit": PAGE_SIZE}, timeout=30,
        )
        resp.raise_for_status()
        items = resp.json().get("data", {}).get("affected_items", [])
        agents.extend(items)
        if len(items) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    log.info("Fetched %d agents", len(agents))
    return agents


# ────────────────────────── Indexer: alerts ──────────────────────────

def fetch_alerts(session, settings, since: str | None) -> list[dict]:
    """Page through alerts using search_after (handles >10k results)."""
    url = f"{settings.indexer_url.rstrip('/')}/{ALERTS_INDEX}/_search"
    auth = (settings.indexer_username, settings.indexer_password)
    query = {"match_all": {}} if not since else {
        "range": {"@timestamp": {"gt": since}}
    }
    body = {
        "size": PAGE_SIZE,
        "query": query,
        "sort": [{"@timestamp": "asc"}, {"_id": "asc"}],
    }
    hits, search_after = [], None
    while True:
        if search_after:
            body["search_after"] = search_after
        resp = _retry(session.post, url, auth=auth, json=body, timeout=60)
        resp.raise_for_status()
        batch = resp.json().get("hits", {}).get("hits", [])
        if not batch:
            break
        hits.extend(batch)
        log.info("Fetched %d alerts (%d total)", len(batch), len(hits))
        if len(batch) < PAGE_SIZE:
            break
        search_after = batch[-1]["sort"]
    return hits


# ────────────────────────── parsing ──────────────────────────

def _parse_ts(value) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "").split("+")[0])
    except ValueError:
        return None


def parse_agent(item: dict) -> dict:
    os_info = item.get("os", {}) or {}
    return {
        "agent_id": str(item.get("id")),
        "name": item.get("name"),
        "ip": item.get("ip"),
        "os_name": os_info.get("name"),
        "os_version": os_info.get("version"),
        "wazuh_version": item.get("version"),
        "status": item.get("status"),
        "last_seen": _parse_ts(item.get("lastKeepAlive")),
    }


def parse_alert(hit: dict) -> dict:
    src = hit.get("_source", hit)
    rule = src.get("rule", {}) or {}
    mitre = rule.get("mitre", {}) or {}
    technique_ids = mitre.get("id") or []
    if isinstance(technique_ids, str):
        technique_ids = [technique_ids]
    agent = src.get("agent", {}) or {}
    decoder = src.get("decoder", {}) or {}
    return {
        "wazuh_alert_id": hit.get("_id") or src.get("id") or "",
        "timestamp": _parse_ts(src.get("@timestamp") or src.get("timestamp")),
        "agent_id": str(agent.get("id")) if agent.get("id") is not None else None,
        "rule_id": str(rule.get("id")) if rule.get("id") is not None else None,
        "rule_level": rule.get("level"),
        "description": rule.get("description"),
        "source": src.get("location") or "wazuh",
        "decoder": decoder.get("name"),
        "mitre_techniques": technique_ids,
        "raw_event": src,
    }


# ────────────────────────── ingestion (upsert) ──────────────────────────

def ingest_agents(db: Session, items: list[dict]) -> dict:
    from backend.app.models import WazuhAgent

    existing = {a.agent_id: a for a in db.query(WazuhAgent).all()}
    inserted = updated = 0
    for raw in items:
        rec = parse_agent(raw)
        if not rec["agent_id"]:
            continue
        cur = existing.get(rec["agent_id"])
        if cur is None:
            db.add(WazuhAgent(**rec))
            inserted += 1
        else:
            for k, v in rec.items():
                setattr(cur, k, v)
            updated += 1
    db.commit()
    return {"inserted": inserted, "updated": updated}


def ingest_alerts(db: Session, hits: list[dict]) -> dict:
    from backend.app.models import WazuhAlert

    existing = {a.wazuh_alert_id for a in db.query(WazuhAlert.wazuh_alert_id).all()}
    inserted = skipped = 0
    for hit in hits:
        rec = parse_alert(hit)
        if not rec["wazuh_alert_id"] or rec["wazuh_alert_id"] in existing:
            skipped += 1
            continue
        db.add(WazuhAlert(**rec))
        existing.add(rec["wazuh_alert_id"])
        inserted += 1
    db.commit()
    return {"inserted": inserted, "skipped_duplicates": skipped}


def determine_since(db: Session, since: str | None, full: bool) -> str | None:
    from backend.app.models import WazuhAlert

    if since or full:
        return since
    latest = db.query(func.max(WazuhAlert.timestamp)).scalar()
    return latest.isoformat() if latest else None


# ────────────────────────── entry point ──────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest Wazuh agents and alerts")
    parser.add_argument("--sample", help="Offline MISP-style fixture {agents, alerts}")
    parser.add_argument("--since", help="Incremental: alerts after this ISO timestamp")
    parser.add_argument("--full", action="store_true", help="Ignore stored state")
    parser.add_argument("--no-enrich", action="store_true")
    args = parser.parse_args()

    settings = get_settings()

    if args.sample:
        log.info("Loading Wazuh fixture from %s", args.sample)
        with open(args.sample, encoding="utf-8") as f:
            data = json.load(f)
        agents, alerts = data.get("agents", []), data.get("alerts", [])
    else:
        if not settings.wazuh_api_url or not settings.indexer_url:
            log.error("WAZUH_API_URL and INDEXER_URL must be set (or use --sample).")
            return 1
        session = _session(settings.wazuh_verify_ssl)
        try:
            token = get_api_token(session, settings)
            agents = fetch_agents(session, settings, token)
        except Exception as exc:  # noqa: BLE001
            log.error("Manager API ingestion failed: %s", exc)
            agents = []
        try:
            with SessionLocal() as db:
                since = determine_since(db, args.since, args.full)
            alerts = fetch_alerts(session, settings, since)
        except Exception as exc:  # noqa: BLE001
            log.error("Indexer ingestion failed: %s", exc)
            alerts = []

    with SessionLocal() as db:
        a_stats = ingest_agents(db, agents)
        l_stats = ingest_alerts(db, alerts)
    log.info("Agents: %s | Alerts: %s", a_stats, l_stats)

    if not args.no_enrich:
        from backend.app.wazuh_enrichment.engine import run_enrichment

        with SessionLocal() as db:
            e_stats = run_enrichment(db)
        log.info("Enrichment: %s", e_stats)

    return 0


if __name__ == "__main__":
    sys.exit(main())
