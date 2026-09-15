"""Response generation (Phase 13.7).

Turns gathered evidence into a natural-language analyst briefing. Uses the
configured LLM provider when available; otherwise produces a deterministic,
evidence-grounded summary. Either way the answer is built only from evidence,
so there is no hallucinated intelligence.
"""

import logging

from backend.app.ai.prompt_templates import SYSTEM_PROMPT, build_prompt

log = logging.getLogger("ai.response")


def _deterministic(evidence: dict) -> str:
    parts = []
    rj = evidence.get("risk_justification")
    if rj:
        parts.append(rj)

    se = evidence.get("supporting_entities") or []
    if se:
        names = ", ".join(str(e.get("id") or e.get("name") or "") for e in se[:8] if e)
        if names:
            parts.append(f"Supporting entities: {names}.")

    rels = evidence.get("graph_relationships") or []
    if rels:
        parts.append("Key relationships: " + "; ".join(str(r) for r in rels[:5]) + ".")

    parts.append(
        f"(Data sources: {', '.join(evidence.get('data_sources', []))}; "
        f"confidence {evidence.get('confidence')}.)"
    )
    return " ".join(p for p in parts if p)


def generate(question: str, evidence: dict, provider=None) -> tuple[str, str]:
    """Return (answer_text, generator_used)."""
    if provider is not None:
        try:
            text = provider.complete(SYSTEM_PROMPT, build_prompt(question, evidence))
            if text and text.strip():
                return text.strip(), provider.name
            log.warning("provider returned empty; using deterministic fallback")
        except Exception as exc:  # noqa: BLE001
            log.warning("provider failed (%s); using deterministic fallback", exc)
    return _deterministic(evidence), "deterministic"
