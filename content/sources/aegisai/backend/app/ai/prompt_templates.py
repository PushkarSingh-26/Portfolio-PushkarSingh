"""Prompt templates for the AI Threat Analyst (Phase 13)."""

import json

SYSTEM_PROMPT = (
    "You are a Tier-3 SOC analyst and CTI researcher for a threat-intelligence "
    "platform. Answer the user's question using ONLY the structured EVIDENCE "
    "provided - never invent CVEs, actors, scores, or relationships. If the "
    "evidence is empty or insufficient, say so plainly. Be concise and "
    "actionable: lead with the answer, cite the supporting entities and graph "
    "relationships from the evidence, and end with a recommended next step. "
    "Do not output JSON; write a short analyst briefing."
)


def build_prompt(question: str, evidence: dict) -> str:
    digest = {
        "intent": evidence.get("intent"),
        "findings": evidence.get("findings"),
        "supporting_entities": evidence.get("supporting_entities"),
        "graph_relationships": evidence.get("graph_relationships"),
        "risk_justification": evidence.get("risk_justification"),
        "data_sources": evidence.get("data_sources"),
        "confidence": evidence.get("confidence"),
    }
    return (
        f"QUESTION:\n{question}\n\n"
        f"EVIDENCE (the only facts you may use):\n"
        f"{json.dumps(digest, indent=2, default=str)}\n\n"
        f"Write the analyst briefing now."
    )
