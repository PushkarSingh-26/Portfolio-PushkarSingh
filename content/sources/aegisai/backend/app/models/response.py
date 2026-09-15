"""Human-in-the-loop response recommendations + audit trail (Phase 19).

`response_recommendations` holds evidence-based response actions (derived from
agent investigations) and their approval/execution state; `response_audit` is an
append-only log of every state transition. No action executes without an explicit
approval recorded here.
"""

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class ResponseRecommendation(Base):
    __tablename__ = "response_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM", index=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # pending -> approved | rejected ; approved -> executed ; executed -> verified | failed
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    execution_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<ResponseRecommendation(id={self.id}, action='{self.action_type}', status='{self.status}')>"


class ResponseAudit(Base):
    __tablename__ = "response_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recommendation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("response_recommendations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    event: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<ResponseAudit(rec={self.recommendation_id}, event='{self.event}', actor='{self.actor}')>"
