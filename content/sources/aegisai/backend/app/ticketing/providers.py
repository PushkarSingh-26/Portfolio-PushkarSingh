"""Ticketing providers (Phase 18.7 / 18.8)."""

import hashlib
import logging

import requests

log = logging.getLogger("ticketing.providers")
TIMEOUT = 30


class TicketProvider:
    name = "base"

    def create_ticket(self, title: str, body: str, severity: str = "HIGH", **extra) -> dict:  # pragma: no cover
        raise NotImplementedError


class MockProvider(TicketProvider):
    name = "mock"

    def create_ticket(self, title, body, severity="HIGH", **extra) -> dict:
        tid = "MOCK-" + hashlib.sha1(f"{title}{extra.get('kind','')}".encode()).hexdigest()[:8].upper()
        return {"provider": "mock", "ticket_id": tid, "status": "created",
                "title": title, "severity": severity, "simulated": True, **extra}


class JiraProvider(TicketProvider):
    name = "jira"

    def __init__(self, url, user, token, project):
        self.url, self.user, self.token, self.project = url.rstrip("/"), user, token, project

    def create_ticket(self, title, body, severity="HIGH", **extra) -> dict:
        r = requests.post(f"{self.url}/rest/api/2/issue", auth=(self.user, self.token),
                          json={"fields": {"project": {"key": self.project}, "summary": title[:250],
                                           "description": body, "issuetype": {"name": "Task"}}},
                          timeout=TIMEOUT)
        r.raise_for_status()
        key = r.json().get("key")
        return {"provider": "jira", "ticket_id": key, "status": "created",
                "url": f"{self.url}/browse/{key}"}


class TheHiveProvider(TicketProvider):
    name = "thehive"

    def __init__(self, url, api_key):
        self.url, self.api_key = url.rstrip("/"), api_key

    def create_ticket(self, title, body, severity="HIGH", **extra) -> dict:
        sev = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 3}.get(severity.upper(), 2)
        r = requests.post(f"{self.url}/api/case", headers={"Authorization": f"Bearer {self.api_key}"},
                          json={"title": title, "description": body, "severity": sev}, timeout=TIMEOUT)
        r.raise_for_status()
        return {"provider": "thehive", "ticket_id": r.json().get("_id"), "status": "created"}


class ShuffleProvider(TicketProvider):
    """Shuffle SOAR via webhook (preferred) or workflow execute API."""

    name = "shuffle"

    def __init__(self, webhook_url="", url="", api_key="", workflow_id=""):
        self.webhook_url = webhook_url.rstrip("/") if webhook_url else ""
        self.url = url.rstrip("/") if url else ""
        self.api_key, self.workflow_id = api_key, workflow_id

    def create_ticket(self, title, body, severity="HIGH", **extra) -> dict:
        payload = {"title": title, "body": body, "severity": severity, **extra}
        if self.webhook_url:
            r = requests.post(self.webhook_url, json=payload, timeout=TIMEOUT)
            r.raise_for_status()
            return {"provider": "shuffle", "status": "triggered", "via": "webhook",
                    "ticket_id": (r.json().get("execution_id") if r.headers.get("content-type", "").startswith("application/json") else "accepted")}
        if self.url and self.workflow_id:
            r = requests.post(f"{self.url}/api/v1/workflows/{self.workflow_id}/execute",
                              headers={"Authorization": f"Bearer {self.api_key}"},
                              json={"execution_argument": payload}, timeout=TIMEOUT)
            r.raise_for_status()
            return {"provider": "shuffle", "status": "triggered", "via": "api",
                    "ticket_id": r.json().get("execution_id")}
        raise RuntimeError("Shuffle provider not configured (set SHUFFLE_WEBHOOK_URL or SHUFFLE_URL)")
