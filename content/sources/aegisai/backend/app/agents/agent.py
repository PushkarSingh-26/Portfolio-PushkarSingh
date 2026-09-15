"""Agentic SOC investigation orchestrator (Phase 14.1 / 14.4).

Pipeline: plan -> execute tools (collect evidence + log) -> blast radius ->
report -> persist. Each agent type (alert/cve/actor/campaign/technique/community)
runs autonomously and produces an auditable, evidence-driven report.
"""

import logging

from sqlalchemy.orm import Session

from backend.app.agents import blast_radius, executor, memory, planner, report_generator

log = logging.getLogger("agents.agent")

# Seed entity used for blast-radius traversal per investigation type.
_BLAST_SEED = {
    "alert": ("alert", "alert_id"),
    "cve": ("cve", "cve_id"),
    "actor": ("actor", "actor_id"),
    "campaign": ("campaign", "campaign_id"),
    "community": ("community", "community_id"),
}


def investigate(db: Session, investigation_type: str, target: dict,
                parent_id: int | None = None) -> dict:
    """Run a full autonomous investigation and persist it."""
    plan = planner.plan(investigation_type, target)
    evidence, tool_calls, _context = executor.execute(plan, db)

    blast = {}
    seed = _BLAST_SEED.get(investigation_type)
    if seed:
        seed_type, key = seed
        if target.get(key) is not None:
            blast = blast_radius.compute(seed_type, target[key], db)

    report = report_generator.build_report(investigation_type, target, evidence, blast, tool_calls)
    target_str = f"{investigation_type}:{next((v for v in target.values() if v is not None), '')}"
    inv = memory.save(
        db, investigation_type=investigation_type, target=target_str, plan=plan,
        tool_calls=tool_calls, evidence=evidence, report=report,
        confidence=report["confidence_score"], parent_id=parent_id,
    )
    return {
        "investigation_id": inv.id,
        "investigation_type": investigation_type,
        "target": target_str,
        "plan": plan,
        "tool_calls": tool_calls,
        "blast_radius": blast,
        "report": report,
        "confidence": report["confidence_score"],
        "parent_id": parent_id,
    }


# ── Typed entrypoints ───────────────────────────────────────

def investigate_alert(db, alert_id: int, parent_id=None) -> dict:
    return investigate(db, "alert", {"alert_id": int(alert_id)}, parent_id)


def investigate_cve(db, cve_id: str, parent_id=None) -> dict:
    return investigate(db, "cve", {"cve_id": cve_id.upper()}, parent_id)


def investigate_actor(db, actor_id: int, name: str | None = None, parent_id=None) -> dict:
    return investigate(db, "actor", {"actor_id": int(actor_id), "name": name}, parent_id)


def investigate_campaign(db, campaign_id: int, name: str | None = None, parent_id=None) -> dict:
    return investigate(db, "campaign", {"campaign_id": int(campaign_id), "name": name}, parent_id)


def investigate_community(db, community_id: int, parent_id=None) -> dict:
    return investigate(db, "community", {"community_id": int(community_id)}, parent_id)


def blast_radius_only(db, entity_type: str, entity_id) -> dict:
    return blast_radius.compute(entity_type, entity_id, db)
