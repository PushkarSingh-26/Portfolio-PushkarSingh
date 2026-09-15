"""Build consolidated CTI enrichment for a CVE.

This is the seam a future Wazuh integration plugs into: given a CVE id (which a
collector would extract from a Wazuh vulnerability-detector alert), return all
intelligence the platform holds. No Wazuh-specific code lives here, so wiring a
real Wazuh feed later requires only an ingestion adapter, not changes here.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.schemas.soc import (
    CVEEnrichment,
    EnrichedEPSS,
    EnrichedKEV,
    EnrichedPriority,
    EnrichedTechnique,
)


def enrich_cve(db: Session, cve_id: str) -> CVEEnrichment:
    from backend.app.models import (
        CVE,
        CorrelationResult,
        EPSSScore,
        KEVEntry,
        PriorityScore,
        Technique,
    )

    cve_id = cve_id.upper()
    cve = db.execute(select(CVE).where(CVE.cve_id == cve_id)).scalar_one_or_none()

    if cve is None:
        return CVEEnrichment(
            cve_id=cve_id,
            found=False,
            summary=f"{cve_id} is not in the local CVE catalog; no enrichment available.",
        )

    techniques = [
        EnrichedTechnique(
            technique_id=row.technique_id,
            name=row.name,
            tactic=row.tactic,
            confidence_score=row.confidence_score,
            confidence_level=row.confidence_level,
        )
        for row in db.execute(
            select(
                CorrelationResult.technique_id,
                Technique.name,
                CorrelationResult.tactic,
                CorrelationResult.confidence_score,
                CorrelationResult.confidence_level,
            )
            .join(Technique, Technique.technique_id == CorrelationResult.technique_id)
            .where(CorrelationResult.cve_id == cve_id)
            .order_by(CorrelationResult.confidence_score.desc())
        ).all()
    ]

    epss_row = db.execute(
        select(EPSSScore).where(EPSSScore.cve_id == cve_id)
    ).scalar_one_or_none()
    epss = (
        EnrichedEPSS(epss_score=epss_row.epss_score, percentile=epss_row.percentile)
        if epss_row
        else None
    )

    kev_row = db.execute(
        select(KEVEntry).where(KEVEntry.cve_id == cve_id)
    ).scalar_one_or_none()
    kev = EnrichedKEV(
        in_kev=kev_row is not None,
        date_added=kev_row.date_added if kev_row else None,
        known_ransomware=kev_row.known_ransomware if kev_row else False,
        due_date=kev_row.due_date if kev_row else None,
    )

    prio_row = db.execute(
        select(PriorityScore).where(PriorityScore.cve_id == cve_id)
    ).scalar_one_or_none()
    priority = (
        EnrichedPriority(
            priority_score=prio_row.priority_score,
            priority_level=prio_row.priority_level,
            explanation=prio_row.explanation,
        )
        if prio_row
        else None
    )

    # One-line SOC summary.
    bits = [f"{cve_id}"]
    if cve.severity:
        bits.append(f"{cve.severity} (CVSS {cve.cvss_score})")
    if priority:
        bits.append(f"priority {priority.priority_score:.0f}/{priority.priority_level}")
    if kev.in_kev:
        bits.append("in CISA KEV")
    if epss:
        bits.append(f"EPSS {epss.epss_score:.2f}")
    if techniques:
        bits.append(f"{len(techniques)} ATT&CK technique(s)")
    summary = " | ".join(bits)

    return CVEEnrichment(
        cve_id=cve_id,
        found=True,
        severity=cve.severity,
        cvss_score=cve.cvss_score,
        description=cve.description,
        attack_techniques=techniques,
        epss=epss,
        kev=kev,
        priority=priority,
        summary=summary,
    )


def recommended_action(enrichments: list[CVEEnrichment]) -> tuple[str | None, float | None, str]:
    """Pick the highest-priority CVE and a recommended SOC action."""
    scored = [
        e for e in enrichments if e.priority is not None
    ]
    if not scored:
        return None, None, "No prioritized CVEs in this alert; triage manually."
    top = max(scored, key=lambda e: e.priority.priority_score)
    in_kev = top.kev and top.kev.in_kev
    if in_kev:
        action = "ESCALATE: KEV-listed (actively exploited). Patch immediately per CISA directive."
    elif top.priority.priority_level in ("CRITICAL", "HIGH"):
        action = "PRIORITIZE: high threat priority - schedule urgent remediation."
    else:
        action = "MONITOR: lower priority - remediate within standard SLA."
    return top.cve_id, top.priority.priority_score, action
