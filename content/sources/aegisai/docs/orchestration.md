# Phase 18 — Autonomous SOC Pipeline & Orchestration

Orchestration-only layer that coordinates the existing (unchanged) components into
one autonomous, scheduled, observable, restart-safe pipeline. Nothing upstream was
redesigned — jobs wrap existing entrypoints.

## Pipeline architecture

```
        APScheduler (opt-in: ORCHESTRATION_ENABLED)
              │  cron triggers (18 jobs)
              ▼
        executor.run_job(name)  ──▶ retry + backoff ──▶ pipeline_runs (history)
              │  (idempotent: engines upsert / dedup)
              ▼
        pipeline.run_pipeline()  ── dependency-ordered ──▶ downstream consumes upstream
              ▼
        monitoring.health()  ──▶ success/failure rate · avg runtime · next runs
```

Files: `backend/app/orchestration/{scheduler,pipeline,jobs,executor,history,monitoring,rules}.py`,
`backend/app/ticketing/{providers,service}.py`.

## Job dependency diagram (internal pipeline)

```
 correlation ─▶ risk_scoring ─▶ graph_sync ─▶ graph_analytics ─▶ graph_intelligence
                                                    │
        ┌───────────────────────────────────────────┘
        ▼
 embeddings ─▶ link_prediction ─▶ coverage ─▶ attack_paths ─▶ autonomous_triage ─▶ daily_briefing
```
External collectors (`wazuh/misp/epss/kev/nvd/mitre_sync`) run as subprocesses and
feed everything upstream; excluded from `/pipeline/run` by default (`include_collectors`).

## Scheduler diagram (production cron)

```
 */15 min  wazuh_sync            04:00  graph_analytics     06:00  risk_scoring
 */30 min  misp_sync             04:15  graph_intelligence  06:30  autonomous_triage
 01:00     epss_sync             04:30  embeddings          08:00  daily_briefing
 01:15     kev_sync              05:00  link_prediction     Mon 09:00 weekly_cti
 02:00     nvd_sync              05:30  coverage
 Sun 03:00 mitre_sync            05:45  attack_paths
 03:15     correlation           03:30  graph_sync
```
(15 spec schedules + `graph_intelligence` and `attack_paths` = 18 jobs total.)

## SOAR integration diagram

```
 autonomous_triage ─▶ agent investigation ─▶ ticketing.export_investigation
                                                    │
        ┌───────────────────────────────────────────┤ provider = env TICKET_PROVIDER
        ▼                 ▼                 ▼         ▼
     MockProvider      JiraProvider    TheHiveProvider   ShuffleProvider
     (default)         REST issue      REST case         webhook or workflow API
```
Shuffle uses `SHUFFLE_WEBHOOK_URL` (preferred) or the workflow execute API. No
provider needs to be live — Mock is the default and all failures fall back to it.

## Retry, recovery & idempotency (18.4)

- `executor.run_job` retries `JOB_MAX_RETRIES` times with linear backoff; every
  attempt's final outcome is a `pipeline_runs` row (running → completed/failed).
- **Idempotent:** correlation/risk/graph/analytics/embeddings/coverage all upsert;
  triage dedups investigations by target; reports append but triage-of-a-given-alert
  won't re-run. So retries and restarts never duplicate data.
- **Resume:** `run_pipeline(resume_from="coverage")` restarts mid-pipeline.
- **Failed-job tracking:** `pipeline_runs.status='failed'` + error/traceback metadata.

## Autonomous investigation rules (18.5)

| Condition | Action |
|---|---|
| Wazuh level ≥ 10, new KEV, EPSS ≥ 0.80, predicted conf > 0.80, new actors/campaigns, critical gaps | **AUTO** investigate (agent) |
| Wazuh level 7–9, EPSS 0.50–0.79 | **QUEUE** (stored in `investigation_queue` report) |
| Wazuh level ≤ 6, EPSS < 0.50 | **IGNORE** (counted) |

## APIs (18.10)

`GET /pipeline/jobs`, `/pipeline/history`, `/pipeline/status`, `/pipeline/health`;
`POST /pipeline/run`, `/pipeline/run/{job}`, `/pipeline/retry/{job}`.

## Deployment

Set `ORCHESTRATION_ENABLED=true` (+ `.env` credentials for live collectors/SOAR) to
start the in-process APScheduler on API boot. For dev/tests it stays off so nothing
auto-runs. Cron/systemd can alternatively invoke `python -m` collectors + the
pipeline API. Everything is observable via `/pipeline/*` and the 6 dashboard pages.
