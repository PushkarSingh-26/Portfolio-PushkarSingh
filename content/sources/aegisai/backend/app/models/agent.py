"""Agentic SOC investigation persistence (Phase 14).

Each autonomous investigation is stored with its plan (task graph), tool-call
log, collected evidence, and final report, plus a self-referential parent_id so
investigation lineage (continue / compare) can be tracked.
"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class AgentInvestigation(Base):
    __tablename__ = "agent_investigations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    investigation_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    target: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed", index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    plan: Mapped[list | None] = mapped_column(JSON, nullable=True)
    tool_calls: Mapped[list | None] = mapped_column(JSON, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("agent_investigations.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<AgentInvestigation(id={self.id}, type='{self.investigation_type}', target='{self.target}')>"
