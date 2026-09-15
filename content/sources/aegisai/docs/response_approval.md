# Phase 19 — Human-in-the-Loop Response (Approval-Gated)

The final engineering phase. Turns evidence-based agent recommendations into
**approvable** response actions that execute **only through the existing
ShuffleProvider** after explicit analyst approval, with verification and a complete
audit trail. No action ever runs automatically. No new external products were
introduced — everything reuses PostgreSQL, the FastAPI backend, the Agentic SOC
Analyst, and the Phase-18 ticketing/SOAR framework.

## Response lifecycle

```
 agent investigation report.recommendations (evidence-cited)
        │  response_engine.generate_from_investigation()  (idempotent)
        ▼
   [ pending ] ──approve(analyst)──▶ [ approved ] ──execute(analyst)──▶ [ executed ]
        │                                │  via ticketing.execute_action()      │
        └──reject(analyst)──▶ [rejected] │  (ShuffleProvider webhook / mock)     │
                                         │                                       ▼
                                         └──────────────── verify(analyst) ─▶ [ verified ]
 every transition appends to response_audit (event, actor, timestamp, detail)
```

The approval gate is enforced in `execute()`: it raises `PermissionError`
(HTTP 409) unless `status == "approved"`. `verify()` likewise requires
`status == "executed"`.

## Data model (2 tables, 1 migration)

- **`response_recommendations`** — action_type, title, description, severity,
  rationale + evidence (JSON), confidence, status, approved_by/at, executed_at,
  verified, execution_result (SOAR response), source (investigation).
- **`response_audit`** — append-only (recommendation_id, event, actor, detail, ts).

`action_type` is mapped deterministically from the agent recommendation text
(patch / escalate / threat_hunt / tune_detection / investigate / monitor / review).

## Backend module

`backend/app/response_engine.py` — `generate_from_investigation`, `generate_recent`,
`list_recommendations`, `approve`, `reject`, `execute`, `verify`, `audit_trail`,
`stats`. Execution reuses `backend.app.ticketing.execute_action()` (added to the
existing service), which routes to Shuffle (webhook/workflow) when configured and
the credential-free Mock otherwise.

## APIs

`GET /response/recommendations`, `/response/recommendations/{id}`,
`/response/recommendations/{id}/audit`, `/response/stats`, `/response/audit`;
`POST /response/generate`, `/response/recommendations/{id}/approve|reject|execute|verify`.

## Dashboard (5 pages)

Response Recommendations · Approval Queue · Action Execution Center ·
Response Audit Trail · SOAR Response Center.

## Guarantees

- **No autonomous execution** — execution requires a prior recorded approval;
  attempting to execute a non-approved recommendation returns 409.
- **Auditable** — every transition (generated/approved/rejected/executed/verified)
  is logged with actor + timestamp in `response_audit`.
- **Reuses SOAR** — execution goes through the existing ShuffleProvider; Mock by
  default so nothing external is required for dev/tests.
- **Idempotent generation** — re-generating from the same investigation creates no
  duplicates.
- **Lightweight** — 2 tables, 1 migration, 1 backend module, 5 dashboard pages.
