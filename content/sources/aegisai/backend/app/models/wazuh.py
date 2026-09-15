"""Wazuh SOC models (Phase 10): agents, alerts, and per-alert enrichment.

Wazuh's own severity (`rule_level`) is preserved verbatim on `wazuh_alerts`.
The CTI platform adds a *separate* `priority_score` in `wazuh_alert_enrichment`
so the SOC view never overwrites Wazuh's native severity.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class WazuhAgent(Base):
    __tablename__ = "wazuh_agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    agent_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    os_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    os_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    wazuh_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<WazuhAgent(agent_id='{self.agent_id}', name='{self.name}')>"


class WazuhAlert(Base):
    __tablename__ = "wazuh_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    wazuh_alert_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    agent_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    rule_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    rule_level: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decoder: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mitre_techniques: Mapped[list | None] = mapped_column(JSON, nullable=True)
    raw_event: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    enrichment: Mapped["WazuhAlertEnrichment | None"] = relationship(
        back_populates="alert", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:
        return f"<WazuhAlert(wazuh_alert_id='{self.wazuh_alert_id}', rule_level={self.rule_level})>"


class WazuhAlertEnrichment(Base):
    """CTI enrichment + SOC priority for one alert.

    The single-value FK columns (technique_id, cve_id, threat_actor_id, ...)
    record the top-signal entity for quick filtering; the full multi-entity
    graph and how each link was derived live in the `evidence` JSON.
    """

    __tablename__ = "wazuh_alert_enrichment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    alert_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("wazuh_alerts.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True,
    )
    technique_id: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    cve_id: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    threat_actor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("threat_actors.id", ondelete="SET NULL"), nullable=True, index=True
    )
    malware_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("malware_families.id", ondelete="SET NULL"), nullable=True, index=True
    )
    campaign_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True, index=True
    )
    epss_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    kev_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    existing_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, index=True)
    priority_level: Mapped[str] = mapped_column(String(10), nullable=False, default="LOW", index=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    alert: Mapped["WazuhAlert"] = relationship(back_populates="enrichment")

    def __repr__(self) -> str:
        return (
            f"<WazuhAlertEnrichment(alert_id={self.alert_id}, "
            f"priority={self.priority_score}/{self.priority_level})>"
        )
