# Phase 10 — Wazuh SOC Integration Architecture

The CTI platform now ingests Wazuh telemetry and turns raw alerts into
threat-prioritized, CTI-enriched SOC events. Wazuh's native severity is never
modified; the platform adds a *separate* SOC priority and an enrichment record.

## Wazuh integration architecture

```
        WAZUH DEPLOYMENT (Docker)                     CTI PLATFORM
 ┌─────────────────────────────────┐      ┌──────────────────────────────────┐
 │ wazuh.manager-1   :55000 (API)  │      │ collectors/wazuh.py              │
 │   • agents, rules, JWT auth     │─────▶│   • JWT auth (env creds)         │
 │ wazuh.indexer-1   :9200 (OS)    │      │   • GET /agents (paginated)      │
 │   • wazuh-alerts-* documents    │─────▶│   • indexer _search (search_after)│
 │ wazuh.dashboard-1 :443          │      │   • retries + SSL toggle          │
 └─────────────────────────────────┘      └───────────────┬──────────────────┘
        credentials via ENV VARS only                      │ upsert
   WAZUH_API_URL / USERNAME / PASSWORD                      ▼
   INDEXER_URL / USERNAME / PASSWORD          ┌──────────────────────────────┐
   WAZUH_VERIFY_SSL                           │ wazuh_agents · wazuh_alerts   │
                                              └───────────────┬──────────────┘
                                                              ▼
                                          backend/app/wazuh_enrichment/engine.py
                                                              ▼
                                              ┌──────────────────────────────┐
                                              │ wazuh_alert_enrichment        │
                                              │  (CTI links + SOC priority)   │
                                              └──────────────────────────────┘
```

## SOC enrichment flow (per alert)

```
 Wazuh alert
     │  rule.mitre.id  →  [ ATT&CK techniques ]
     ▼
 technique ──(correlation_results)──▶ CVEs
     │                                  │
     │                                  ├──(epss_scores)────▶ EPSS probability
     │                                  ├──(kev_entries)────▶ KEV (exploited?)
     │                                  ├──(risk_scores)────▶ existing ML risk
     │                                  └──(cti_relationships)
     │                                        actor ◀── exploits_cve
     ▼                                          │
 evidence{techniques, cves[], epss, kev,        ├── uses_malware ──▶ malware
          risk, actors, malware, campaigns}     └── attributed ───▶ campaign
     ▼
 SOC Priority Engine  →  priority_score (0-100) + level (CRITICAL/HIGH/MEDIUM/LOW)
     ▼
 wazuh_alert_enrichment row (one per alert, explainable evidence stored)
```

All correlation/EPSS/KEV/actor links reuse the existing CTI tables — no data is
re-derived. Every enrichment stores the evidence and a human-readable rationale.

## SOC Priority methodology

Wazuh severity (`rule_level`, 0-15) is preserved verbatim. The SOC priority is a
*separate* 0-100 score:

```
base = 100 * ( 0.25 * wazuh_severity     (rule_level / 15)
             + 0.20 * existing_risk       (max ML risk of related CVEs / 100)
             + 0.20 * epss                (max EPSS of related CVEs)
             + 0.15 * cve_breadth         (min(#related_cves, 5) / 5)
             + 0.10 * technique_breadth   (min(#techniques, 5) / 5)
             + 0.10 * actor_present )
```

CISA KEV override: if any related CVE is KEV-listed, `final = min(100, max(base,75)+15)`
— confirmed in-the-wild exploitation against a monitored asset is the strongest
escalation. Levels: CRITICAL ≥ 75, HIGH ≥ 50, MEDIUM ≥ 25, LOW < 25.

## SOC workflow

1. Alerts and agents sync from Wazuh (initial + incremental via `--since` /
   stored max timestamp).
2. Every alert is enriched and assigned a SOC priority with stored evidence.
3. Analysts work the **Priority Queue** (dashboard) — KEV-linked and
   actor-attributed alerts rise to the top regardless of raw Wazuh level.
4. Each alert exposes its full enrichment (techniques → CVEs → EPSS/KEV →
   actor → malware/campaign) and a plain-English rationale for triage.

## Credentials

All Wazuh/Indexer credentials are read from environment variables; nothing is
hardcoded. Live ingestion requires `WAZUH_API_URL`, `WAZUH_USERNAME`,
`WAZUH_PASSWORD`, `INDEXER_URL`, `INDEXER_USERNAME`, `INDEXER_PASSWORD`, and
`WAZUH_VERIFY_SSL`. For offline verification, `collectors/wazuh.py --sample`
loads a MISP/Wazuh-shaped JSON fixture through the identical parser/enrichment.
```
```
