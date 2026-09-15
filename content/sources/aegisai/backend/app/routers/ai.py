"""AI Threat Analyst API (Phase 13.8).

Structured-JSON endpoints for natural-language investigation. Answers are
grounded in real platform evidence; with no LLM configured the analyst returns
deterministic evidence summaries.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.ai import analyst
from backend.app.database import get_db
from backend.app.schemas import (
    ActorRequest,
    AIChatRequest,
    AIQueryRequest,
    AIResponse,
    AlertRequest,
    CampaignRequest,
    CVERequest,
)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/query", response_model=AIResponse)
def ai_query(payload: AIQueryRequest, db: Session = Depends(get_db)):
    """Answer a natural-language investigation question."""
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="question must not be empty")
    return analyst.ask(payload.question, db, payload.session_id)


@router.post("/chat", response_model=AIResponse)
def ai_chat(payload: AIChatRequest, db: Session = Depends(get_db)):
    """Multi-turn chat: same engine, with per-session memory for follow-ups."""
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")
    return analyst.ask(payload.message, db, payload.session_id)


@router.post("/investigate/alert", response_model=AIResponse)
def investigate_alert(payload: AlertRequest, db: Session = Depends(get_db)):
    return analyst.investigate_alert(payload.alert_id, db)


@router.post("/investigate/cve", response_model=AIResponse)
def investigate_cve(payload: CVERequest, db: Session = Depends(get_db)):
    return analyst.investigate_cve(payload.cve_id, db)


@router.post("/investigate/actor", response_model=AIResponse)
def investigate_actor(payload: ActorRequest, db: Session = Depends(get_db)):
    return analyst.investigate_actor(payload.actor_id, db, payload.name)


@router.post("/investigate/campaign", response_model=AIResponse)
def investigate_campaign(payload: CampaignRequest, db: Session = Depends(get_db)):
    return analyst.investigate_campaign(payload.campaign_id, db, payload.name)


@router.post("/investigate/path", response_model=AIResponse)
def investigate_path(payload: AlertRequest, db: Session = Depends(get_db)):
    return analyst.investigate_path(payload.alert_id, db)
