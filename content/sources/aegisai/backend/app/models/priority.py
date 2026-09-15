from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class PriorityScore(Base):
    """Threat-prioritization score (v2) combining all available signals.

    Extends - does not replace - the ML risk score. It blends CVSS, correlation
    confidence, the ML risk score, EPSS exploit probability, ATT&CK relationship
    strength, and CISA KEV presence into a single 0-100 priority with an
    explainable per-component breakdown stored alongside it.
    """

    __tablename__ = "priority_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    cve_id: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("cves.cve_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    priority_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    priority_level: Mapped[str] = mapped_column(String(10), nullable=False, index=True)

    # Snapshots of the input signals (for transparency + old/new comparison).
    ml_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    epss_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    kev_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    # Per-component point contributions (sum ~= priority_score) for explainability.
    comp_cvss: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    comp_correlation: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    comp_ml: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    comp_epss: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    comp_attack: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    comp_kev: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    method: Mapped[str] = mapped_column(String(50), nullable=False, default="priority-v2")

    generated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<PriorityScore(cve_id='{self.cve_id}', "
            f"priority_score={self.priority_score}, level='{self.priority_level}')>"
        )
