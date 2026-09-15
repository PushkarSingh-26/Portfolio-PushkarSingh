# Phase 8.4 — Wazuh Readiness Layer: Architecture & Future Integration

**Status: FOUNDATION ONLY.** No live Wazuh instance is deployed or contacted in
this phase. This document describes the future ingestion, enrichment, and SOC
workflows, and how the foundation already built (the `/soc/*` API and the
`backend/app/soc/enrichment.py` service) makes that integration a small,
additive change.

## What exists today (the seam)

- **Enrichment service** — `enrich_cve(db, cve_id)` consolidates everything the
  platform knows about a CVE: ATT&CK techniques (with tactic + confidence),
  EPSS, KEV status, and the v2 priority score + explanation, plus a one-line
  SOC summary.
- **SOC API** (`/soc`):
  - `GET /soc/enrich/{cve_id}` — enrichment for a single CVE.
  - `POST /soc/enrich` — accepts a minimal alert (`cve_ids`, optional `rule_id`,
    `agent_name`) and returns every CVE enriched plus the highest-priority CVE
    and a recommended action.
  - `GET /soc/demo-alert` — a sample enriched alert (used by the dashboard SOC
    Readiness page) showing the end-to-end result.

Crucially, none of this contains Wazuh-specific code. The enrichment layer
speaks "CVE id in → consolidated intelligence out", so adding Wazuh later means
writing only an **ingestion adapter** that extracts CVE ids from Wazuh alerts.

## Future ingestion flow

```
Wazuh Indexer / Wazuh API  ──►  CTI ingestion adapter  ──►  POST /soc/enrich
   (vulnerability-detector        (new, ~1 module:            (already exists)
    alerts, rule groups            map alert → cve_ids)
    vulnerability-detector)
```

1. A scheduled adapter polls the Wazuh Indexer (`wazuh-alerts-*`) or subscribes
   to the Wazuh API for alerts whose `rule.groups` include
   `vulnerability-detector`, or whose `data.vulnerability.cve` is populated.
2. The adapter extracts the CVE id(s) and the alert's `rule.id` / `agent.name`.
3. It calls `POST /soc/enrich` (in-process or over HTTP) and receives the
   enriched alert.

Only step 1–2 are new; they require no change to the enrichment layer or schema.

## Future enrichment flow

```
raw Wazuh alert ──► extract CVE(s) ──► enrich_cve() per CVE ──► EnrichedAlert
                                          │
              ┌───────────────┬───────────┼───────────────┬──────────────┐
           ATT&CK          related        EPSS            KEV          priority
        techniques+tactic   CVEs       probability   exploited?+due    score+why
```

The `EnrichedAlert` carries, for each CVE: severity/CVSS, mapped ATT&CK
techniques, EPSS probability, KEV status (with CISA due date and ransomware
flag), and the explainable priority score — plus a single `recommended_action`
(ESCALATE / PRIORITIZE / MONITOR) derived from the highest-priority CVE.

## Future SOC workflow

1. **Alert fires** in Wazuh (e.g. vulnerability-detector flags `CVE-XXXX` on an
   asset).
2. **Auto-enrichment** annotates the alert/case with ATT&CK context, EPSS, KEV,
   and the priority score + explanation.
3. **Triage by priority, not raw CVSS.** Analysts work the queue ordered by the
   v2 priority. KEV-listed and high-EPSS items surface to the top; the long tail
   of high-CVSS-but-low-exploitability CVEs correctly drops down.
4. **Action routing.** `recommended_action` drives the playbook: KEV →
   immediate patch per CISA directive; CRITICAL/HIGH priority → urgent
   remediation; otherwise standard SLA.
5. **Write-back** (future): push enrichment + priority into the Wazuh case or a
   SOAR ticket so the verdict lives with the alert.

## Write-back options (future)

- Wazuh Indexer document enrichment (add a `cti.*` field set to the alert doc).
- Wazuh Active Response / integrator hook to call the CTI API on alert.
- SOAR (e.g. Shuffle/TheHive) step that calls `POST /soc/enrich` and attaches
  the result to the case.

## Why this requires minimal change later

| Concern | Handled by | Change needed for Wazuh |
|---|---|---|
| Consolidating CTI for a CVE | `enrich_cve()` | none |
| Alert-shaped request/response | `WazuhAlertEnrichRequest` / `EnrichedAlert` | none |
| Priority + recommended action | priority engine + `recommended_action()` | none |
| Getting CVE ids out of Wazuh | — | one ingestion adapter (new) |
| Writing results back | — | one write-back adapter (optional) |

The CTI brain is built; only the Wazuh-specific I/O adapters remain for a future
phase.
