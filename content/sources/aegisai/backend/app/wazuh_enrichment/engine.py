"""Alert enrichment and SOC priority scoring.

SOC Priority methodology (deterministic + explainable)
------------------------------------------------------
Wazuh severity is preserved; this is a *separate* 0-100 SOC priority that fuses
the alert's own severity with the CTI the platform already holds:

    base = 100 * ( 0.25 * wazuh_severity      (rule_level / 15)
                 + 0.20 * existing_risk        (max ML risk of related CVEs /100)
                 + 0.20 * epss                 (max EPSS of related CVEs)
                 + 0.15 * cve_breadth          (min(#related_cves,5)/5)
                 + 0.10 * technique_breadth    (min(#techniques,5)/5)
                 + 0.10 * actor_present )

CISA KEV is a real-world override: if any related CVE is KEV-listed the alert is
floored to >= 75 and boosted, because confirmed in-the-wild exploitation against
a monitored asset is the strongest escalation signal. Levels: CRITICAL >= 75,
HIGH >= 50, MEDIUM >= 25, LOW < 25.
"""

from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

KEV_FLOOR = 75.0
KEV_BOOST = 15.0
MAX_CVE_EVIDENCE = 25


def priority_level(score: float) -> str:
    if score >= 75:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "MEDIUM"
    return "LOW"


def compute_alert_priority(signals: dict) -> dict:
    """Pure SOC-priority function. Returns score, level, and a rationale."""
    sev_n = min(max(signals.get("rule_level", 0) / 15.0, 0.0), 1.0)
    risk_n = min(max(signals.get("max_risk", 0.0) / 100.0, 0.0), 1.0)
    epss_n = min(max(signals.get("max_epss", 0.0), 0.0), 1.0)
    cve_n = min(signals.get("num_cves", 0), 5) / 5.0
    tech_n = min(signals.get("num_techniques", 0), 5) / 5.0
    actor = 1.0 if signals.get("actor_present") else 0.0
    kev = bool(signals.get("kev_present"))

    comp = {
        "wazuh_severity": round(0.25 * sev_n * 100, 2),
        "existing_risk": round(0.20 * risk_n * 100, 2),
        "epss": round(0.20 * epss_n * 100, 2),
        "cve_breadth": round(0.15 * cve_n * 100, 2),
        "technique_breadth": round(0.10 * tech_n * 100, 2),
        "actor_present": round(0.10 * actor * 100, 2),
    }
    base = sum(comp.values())
    if kev:
        final = min(100.0, max(base, KEV_FLOOR) + KEV_BOOST)
        comp["kev_override"] = round(final - base, 2)
    else:
        final = base
        comp["kev_override"] = 0.0
    final = round(min(final, 100.0), 2)

    reasons = []
    if kev:
        reasons.append("related CVE is in CISA KEV (actively exploited)")
    if signals.get("actor_present"):
        reasons.append(f"attributed threat actor(s): {', '.join(signals.get('actors', [])[:3])}")
    if epss_n >= 0.3:
        reasons.append(f"high EPSS ({epss_n:.2f})")
    if signals.get("num_cves"):
        reasons.append(f"{signals['num_cves']} related CVE(s)")
    reasons.append(f"Wazuh level {signals.get('rule_level', 0)}")
    rationale = f"SOC priority {final:.0f} ({priority_level(final)}): " + "; ".join(reasons)

    return {"priority_score": final, "priority_level": priority_level(final),
            "components": comp, "rationale": rationale}


def _load_cti(db: Session):
    """Preload the CTI lookup maps used to enrich every alert."""
    from backend.app.models import (
        CTIRelationship,
        Campaign,
        CorrelationResult,
        CVE,
        EPSSScore,
        KEVEntry,
        MalwareFamily,
        RiskScore,
        ThreatActor,
    )

    tech_to_cves = defaultdict(list)
    for tech, cve, conf in db.execute(
        select(CorrelationResult.technique_id, CorrelationResult.cve_id,
               CorrelationResult.confidence_score)
    ).all():
        tech_to_cves[tech].append((cve, conf))

    epss = {c: s for c, s in db.execute(select(EPSSScore.cve_id, EPSSScore.epss_score)).all()}
    kev = {row[0] for row in db.execute(select(KEVEntry.cve_id)).all()}
    risk = {c: s for c, s in db.execute(select(RiskScore.cve_id, RiskScore.risk_score)).all()}
    valid_techniques = {row[0] for row in db.execute(select(CorrelationResult.technique_id).distinct()).all()}

    # CVE -> actor names (via CTI relationships actor<->cve, either direction).
    cve_to_actors = defaultdict(set)
    rels = db.execute(
        select(CTIRelationship.source_type, CTIRelationship.source_key,
               CTIRelationship.target_type, CTIRelationship.target_key)
    ).all()
    actor_to_malware = defaultdict(set)
    actor_to_campaign = defaultdict(set)
    for st, sk, tt, tk in rels:
        if {st, tt} == {"actor", "cve"}:
            actor = sk if st == "actor" else tk
            cve = sk if st == "cve" else tk
            cve_to_actors[cve].add(actor)
        elif st == "actor" and tt == "malware":
            actor_to_malware[sk].add(tk)
        elif st == "actor" and tt == "campaign":
            actor_to_campaign[sk].add(tk)

    actor_ids = {a.actor_name: a.id for a in db.query(ThreatActor).all()}
    malware_ids = {m.malware_name: m.id for m in db.query(MalwareFamily).all()}
    campaign_ids = {c.campaign_name: c.id for c in db.query(Campaign).all()}

    return {
        "tech_to_cves": tech_to_cves, "epss": epss, "kev": kev, "risk": risk,
        "valid_techniques": valid_techniques, "cve_to_actors": cve_to_actors,
        "actor_to_malware": actor_to_malware, "actor_to_campaign": actor_to_campaign,
        "actor_ids": actor_ids, "malware_ids": malware_ids, "campaign_ids": campaign_ids,
    }


def enrich_alert(alert, cti: dict) -> dict:
    """Build the enrichment row payload for a single alert."""
    techniques = [t for t in (alert.mitre_techniques or []) if t in cti["valid_techniques"]]

    cve_rows, actors = [], set()
    seen_cves = set()
    for tech in techniques:
        for cve, conf in cti["tech_to_cves"].get(tech, []):
            if cve in seen_cves:
                continue
            seen_cves.add(cve)
            cve_rows.append({
                "cve_id": cve,
                "epss": cti["epss"].get(cve),
                "kev": cve in cti["kev"],
                "risk": cti["risk"].get(cve),
                "via_technique": tech,
                "confidence": round(conf, 3),
            })
            actors.update(cti["cve_to_actors"].get(cve, set()))

    malware, campaigns = set(), set()
    for a in actors:
        malware.update(cti["actor_to_malware"].get(a, set()))
        campaigns.update(cti["actor_to_campaign"].get(a, set()))

    max_epss = max([r["epss"] for r in cve_rows if r["epss"] is not None], default=0.0)
    max_risk = max([r["risk"] for r in cve_rows if r["risk"] is not None], default=0.0)
    kev_present = any(r["kev"] for r in cve_rows)

    signals = {
        "rule_level": alert.rule_level or 0,
        "max_risk": max_risk, "max_epss": max_epss, "kev_present": kev_present,
        "num_cves": len(cve_rows), "num_techniques": len(techniques),
        "actor_present": bool(actors), "actors": sorted(actors),
    }
    prio = compute_alert_priority(signals)

    # Confidence: blend of evidence coverage and mean correlation confidence.
    mean_conf = (sum(r["confidence"] for r in cve_rows) / len(cve_rows)) if cve_rows else 0.0
    coverage = sum(bool(x) for x in (techniques, cve_rows, actors, kev_present)) / 4.0
    confidence = round(min(1.0, 0.5 * mean_conf + 0.5 * coverage), 3)

    top_actor = sorted(actors)[0] if actors else None
    top_malware = sorted(malware)[0] if malware else None
    top_campaign = sorted(campaigns)[0] if campaigns else None
    # Top CVE = highest existing risk, else highest EPSS.
    top_cve = None
    if cve_rows:
        top_cve = sorted(
            cve_rows, key=lambda r: (r["risk"] or 0, r["epss"] or 0), reverse=True
        )[0]["cve_id"]

    evidence = {
        "techniques": techniques,
        "cves": cve_rows[:MAX_CVE_EVIDENCE],
        "cve_count": len(cve_rows),
        "threat_actors": sorted(actors),
        "malware": sorted(malware),
        "campaigns": sorted(campaigns),
        "signals": signals,
        "priority_components": prio["components"],
        "rationale": prio["rationale"],
    }

    return {
        "technique_id": techniques[0] if techniques else None,
        "cve_id": top_cve,
        "threat_actor_id": cti["actor_ids"].get(top_actor) if top_actor else None,
        "malware_id": cti["malware_ids"].get(top_malware) if top_malware else None,
        "campaign_id": cti["campaign_ids"].get(top_campaign) if top_campaign else None,
        "epss_score": round(max_epss, 5) if max_epss else None,
        "kev_present": kev_present,
        "existing_risk_score": round(max_risk, 2) if max_risk else None,
        "priority_score": prio["priority_score"],
        "priority_level": prio["priority_level"],
        "confidence_score": confidence,
        "evidence": evidence,
    }


def run_enrichment(db: Session) -> dict:
    """Enrich every alert and upsert one enrichment row per alert."""
    from backend.app.models import WazuhAlert, WazuhAlertEnrichment

    cti = _load_cti(db)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    existing = {e.alert_id: e for e in db.query(WazuhAlertEnrichment).all()}

    inserted = updated = 0
    by_level = defaultdict(int)
    for alert in db.query(WazuhAlert).all():
        payload = enrich_alert(alert, cti)
        by_level[payload["priority_level"]] += 1
        current = existing.get(alert.id)
        if current is None:
            db.add(WazuhAlertEnrichment(alert_id=alert.id, created_at=now, **payload))
            inserted += 1
        else:
            for k, v in payload.items():
                setattr(current, k, v)
            current.created_at = now
            updated += 1

    db.commit()
    return {
        "enriched": inserted + updated, "inserted": inserted, "updated": updated,
        "by_priority": dict(by_level),
    }


def main() -> int:
    from backend.app.database import SessionLocal

    print("Enriching Wazuh alerts ...")
    with SessionLocal() as db:
        stats = run_enrichment(db)
    print(f"Done. {stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
