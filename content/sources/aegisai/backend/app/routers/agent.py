"""Agentic SOC Analyst API (Phase 14.9)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.agents import agent, memory
from backend.app.agents.tools import TOOL_REGISTRY
from backend.app.database import get_db
from backend.app.schemas import (
    ActorReq,
    AgentResult,
    AlertReq,
    BlastRadiusReq,
    CampaignReq,
    CVEReq,
    HistoryItem,
    InvestigateRequest,
    ReportReq,
)

router = APIRouter(prefix="/agent", tags=["agent"])

_VALID_TYPES = {"alert", "cve", "actor", "campaign", "technique", "community"}


@router.post("/investigate", response_model=AgentResult)
def investigate(payload: InvestigateRequest, db: Session = Depends(get_db)):
    if payload.investigation_type not in _VALID_TYPES:
        raise HTTPException(status_code=400,
                            detail=f"Invalid type. Expected one of {sorted(_VALID_TYPES)}.")
    try:
        return agent.investigate(db, payload.investigation_type, payload.target, payload.parent_id)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/investigate/alert", response_model=AgentResult)
def investigate_alert(payload: AlertReq, db: Session = Depends(get_db)):
    return agent.investigate_alert(db, payload.alert_id, payload.parent_id)


@router.post("/investigate/cve", response_model=AgentResult)
def investigate_cve(payload: CVEReq, db: Session = Depends(get_db)):
    return agent.investigate_cve(db, payload.cve_id, payload.parent_id)


@router.post("/investigate/actor", response_model=AgentResult)
def investigate_actor(payload: ActorReq, db: Session = Depends(get_db)):
    return agent.investigate_actor(db, payload.actor_id, payload.name, payload.parent_id)


@router.post("/investigate/campaign", response_model=AgentResult)
def investigate_campaign(payload: CampaignReq, db: Session = Depends(get_db)):
    return agent.investigate_campaign(db, payload.campaign_id, payload.name, payload.parent_id)


@router.post("/blast-radius")
def blast_radius(payload: BlastRadiusReq, db: Session = Depends(get_db)):
    return agent.blast_radius_only(db, payload.entity_type, payload.entity_id)


@router.post("/report")
def report(payload: ReportReq, db: Session = Depends(get_db)):
    inv = memory.get(db, payload.investigation_id)
    if inv is None:
        raise HTTPException(status_code=404, detail=f"Investigation {payload.investigation_id} not found")
    return {"investigation_id": inv.id, "investigation_type": inv.investigation_type,
            "target": inv.target, "confidence": inv.confidence, "plan": inv.plan,
            "tool_calls": inv.tool_calls, "report": inv.report,
            "lineage": [i.id for i in memory.lineage(db, inv.id)]}


@router.get("/tasks")
def tasks(limit: int = 5, db: Session = Depends(get_db)):
    """Available tools + recent investigation task graphs."""
    recent = memory.history(db, limit=limit)
    return {
        "tools": [{"name": n, "description": d} for n, (_fn, d) in TOOL_REGISTRY.items()],
        "recent_task_graphs": [
            {"investigation_id": i.id, "type": i.investigation_type, "target": i.target,
             "plan": i.plan, "tool_calls": i.tool_calls} for i in recent
        ],
    }


@router.get("/history", response_model=list[HistoryItem])
def history(limit: int = 50, investigation_type: str | None = None, db: Session = Depends(get_db)):
    rows = memory.history(db, limit=limit, investigation_type=investigation_type)
    return [
        HistoryItem(
            id=i.id, investigation_type=i.investigation_type, target=i.target,
            confidence=i.confidence,
            risk_level=(i.report or {}).get("risk_assessment", {}).get("level"),
            parent_id=i.parent_id, created_at=i.created_at,
        ) for i in rows
    ]
