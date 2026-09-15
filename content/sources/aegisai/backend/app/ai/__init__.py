"""AI Threat Analyst (Phase 13).

A Tier-3 SOC/CTI analyst that answers natural-language investigation questions
by gathering real evidence from the platform (Neo4j graph, graph analytics,
attack paths, Wazuh alerts, MISP, CVE/EPSS/KEV, ML risk) and narrating it.

Provider-agnostic: with no LLM configured it produces deterministic,
evidence-grounded answers; Gemini/OpenAI/Ollama plug in via environment config.
Answers are always grounded in gathered evidence - no hallucinated intelligence.
"""
