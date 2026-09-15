"""Ticketing service: provider selection + export helpers (Phase 18.7 / 18.8)."""

import logging

from backend.app.config import get_settings
from backend.app.ticketing.providers import (
    JiraProvider,
    MockProvider,
    ShuffleProvider,
    TheHiveProvider,
)

log = logging.getLogger("ticketing.service")


def get_provider():
    s = get_settings()
    provider = (s.ticket_provider or "mock").lower()
    try:
        if provider == "jira" and s.jira_url and s.jira_token:
            return JiraProvider(s.jira_url, s.jira_user, s.jira_token, s.jira_project)
        if provider == "thehive" and s.thehive_url and s.thehive_api_key:
            return TheHiveProvider(s.thehive_url, s.thehive_api_key)
        if provider == "shuffle" and (s.shuffle_webhook_url or (s.shuffle_url and s.shuffle_workflow_id)):
            return ShuffleProvider(s.shuffle_webhook_url, s.shuffle_url, s.shuffle_api_key, s.shuffle_workflow_id)
    except Exception as exc:  # noqa: BLE001
        log.warning("ticket provider init failed (%s); using mock", exc)
    return MockProvider()


def _safe_create(title, body, severity, **extra) -> dict:
    try:
        return get_provider().create_ticket(title, body, severity, **extra)
    except Exception as exc:  # noqa: BLE001
        log.warning("ticket creation failed (%s); using mock", exc)
        return MockProvider().create_ticket(title, body, severity, **extra)


def create_ticket(title: str, body: str, severity: str = "HIGH", **extra) -> dict:
    return _safe_create(title, body, severity, kind="ticket", **extra)


def export_investigation(investigation: dict) -> dict:
    """Push an agent investigation report to the ticketing/SOAR provider."""
    rep = investigation.get("report", {})
    ra = rep.get("risk_assessment", {})
    title = f"[{ra.get('level', 'INVESTIGATION')}] {investigation.get('target', 'investigation')}"
    body = rep.get("executive_summary", "")
    return _safe_create(title, body, ra.get("level", "HIGH"), kind="investigation",
                        investigation_id=investigation.get("investigation_id"))


def export_report(report: dict, report_type: str = "report") -> dict:
    """Push a SOC briefing / CTI report to the ticketing/SOAR provider."""
    title = f"[{report_type}] CTI report"
    summary = report.get("summary") or report.get("executive_summary") or str(list(report.keys()))
    return _safe_create(title, str(summary)[:2000], "MEDIUM", kind="report", report_type=report_type)


def execute_action(action: dict) -> dict:
    """Execute an APPROVED response action via the SOAR provider (Phase 19).

    Reuses the existing provider framework (Shuffle webhook/workflow when
    configured, mock otherwise). This never runs automatically - callers must
    have recorded analyst approval first.
    """
    title = f"[RESPONSE:{action.get('action_type', 'action')}] {action.get('title', '')}"[:250]
    body = action.get("description", "")
    return _safe_create(title, body, action.get("severity", "HIGH"),
                        kind="response_action", action_type=action.get("action_type"),
                        recommendation_id=action.get("recommendation_id"),
                        source=f"{action.get('source_type')}:{action.get('source_id')}")
