# Phase 14 — Agentic SOC Analyst

Turns the AI Threat Analyst into an autonomous agent that **investigates,
correlates, prioritizes, explains, and recommends** by chaining existing
platform services as vetted tools. Every investigation is evidence-driven and
fully auditable (plan + tool-call log + evidence + report persisted).

## Agent architecture

```
  User Request (type + target)
        ▼
   planner.plan() ───────────▶ Task Graph (ordered steps + rationale + $params)
        ▼
   executor.execute() ───────▶ resolve $params from running context
        │                       run vetted tool (tools.run_tool)  ──┐
        │                       log every call (auditable)          │ TOOL REGISTRY
        ▼                       collect evidence                    │ (12 read-only tools
   blast_radius.compute() ────▶ graph-driven impact surface        │  over existing services)
        ▼                                                          ─┘
   report_generator.build_report()
        │   risk explanation · remediation (evidence-cited) · attack paths · blast radius
        ▼
   memory.save()  ───────────▶ agent_investigations (plan, tool_calls, evidence, report, lineage)
        ▼
   AgentResult (structured, exportable JSON)
```

Files: `backend/app/agents/{agent,planner,executor,memory,tools,report_generator,blast_radius}.py`.

## Tools implemented (12, all read-only over existing services)

`graph_investigation`, `attack_path_investigation`, `alert_investigation`,
`threat_actor_investigation`, `campaign_investigation`, `technique_investigation`,
`risk_score_retrieval`, `graph_metrics_retrieval`, `wazuh_alert_retrieval`,
`misp_intel_retrieval`, `kev_retrieval`, `epss_retrieval`. The agent can act
**only** through this registry (`run_tool` rejects anything else); every call is
logged with status, summary, and duration.

## Planner workflow diagram

```
 investigate alert #N  ──▶  1 wazuh_alert_retrieval
                            2 alert_investigation        (→ derives $cve_id)
                            3 attack_path_investigation
                            4 risk_score_retrieval($cve_id)
                            5 epss_retrieval($cve_id)
                            6 kev_retrieval($cve_id)
                            7 graph_metrics_retrieval(CVE,$cve_id)
                            8 misp_intel_retrieval($cve_id)
```
Steps with `$placeholders` are resolved by the executor from earlier outputs;
unresolved steps are skipped (logged), never fabricated.

## Investigation types (14.4)

Alert, CVE, Threat-Actor, Campaign, Technique, Community — each an autonomous
agent that gathers evidence and produces a full report.

## Blast-radius diagram (14.5)

```
        seed entity
            │  (bounded Neo4j traversal, depth ≤4, undirected)
   ┌────────┼─────────┬──────────┬───────────┬─────────────┐
 alerts    CVEs   techniques   actors    campaigns    communities (from cache)
```
Community seeds read members from cached `graph_metrics`. Output: per-category
counts + capped member lists + total affected.

## Risk explanation & remediation (14.6 / 14.7)

The report's `risk_assessment` explains the level from Wazuh severity + EPSS +
KEV + ML risk + SOC priority + graph centrality. `recommendations` are generated
from that evidence (Patch immediately if KEV; prioritize if high EPSS; escalate
if CRITICAL/HIGH; hunt actor TTPs; tune detections; investigate related alerts)
and **each recommendation cites the evidence tool** it came from. No hallucinated
remediation.

## Investigation report (14.8) — exportable JSON

`executive_summary`, `technical_findings`, `threat_intelligence`,
`attack_path_analysis`, `risk_assessment`, `blast_radius`, `recommendations`,
`confidence_score`, `evidence_sources`.

## Investigation lifecycle diagram (memory, 14.11)

```
 run ─▶ persist (agent_investigations: plan, tool_calls, evidence, report)
   │                                    │ parent_id
   ├─ history  (list past runs)         ├─ continue  (new run, parent_id=prev)
   ├─ report   (fetch stored)           ├─ lineage   (walk parent chain)
   └─ compare  (two runs side by side)  ┘
```

## APIs (14.9)

`POST /agent/investigate`, `/agent/investigate/{alert,cve,actor,campaign}`,
`POST /agent/blast-radius`, `POST /agent/report`, `GET /agent/tasks`,
`GET /agent/history`.

## Security controls

- Agent acts only through the vetted tool registry (no arbitrary code/queries);
  graph tools reuse the parameterized services and read-only Cypher templates.
- Tool failures degrade to skipped/error steps; the agent never crashes or invents data.
- Every recommendation and finding is traceable to a logged tool call + evidence source.
- Full audit trail persisted per investigation (plan, tool-call log, evidence, report).
- Deterministic by default; no external LLM required (optional narration only).
