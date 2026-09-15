"""Cyber Threat Intelligence Platform - Streamlit dashboard.

Reads exclusively from the platform's REST API (no direct DB access), so the
dashboard stays decoupled from the database and reuses the same logic the API
serves. Set CTI_API_URL to point at a non-default API location.

Run:
    streamlit run dashboard/app.py
"""

import math
import os
from collections import defaultdict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

try:  # `streamlit run dashboard/app.py` puts dashboard/ on sys.path, not the root
    from dashboard import ui
except ImportError:  # pragma: no cover - depends on how the app is launched
    import ui

API_BASE = os.getenv("CTI_API_URL", "http://127.0.0.1:8000").rstrip("/")
TIMEOUT = 15

LEVEL_COLORS = {
    "CRITICAL": "#b91c1c",
    "HIGH": "#ea580c",
    "MEDIUM": "#d97706",
    "LOW": "#16a34a",
    "UNSCORED": "#6b7280",
    "Unknown": "#6b7280",
}

st.set_page_config(
    page_title="CTI Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)
ui.inject_theme()


@st.cache_data(ttl=60)
def api_get(path: str, params: dict | None = None):
    """GET JSON from the API. Returns (data, error_message)."""
    try:
        resp = requests.get(f"{API_BASE}{path}", params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as exc:
        return None, str(exc)


def api_post(path: str, body: dict, timeout: int = 120):
    """POST JSON to the API. Returns (data, error_message)."""
    try:
        resp = requests.post(f"{API_BASE}{path}", json=body, timeout=timeout)
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as exc:
        return None, str(exc)


def require(path: str, params: dict | None = None):
    """Fetch or render an error + stop the page."""
    data, err = api_get(path, params)
    if err is not None:
        st.error(f"Could not reach the API at {API_BASE}{path}.\n\n{err}")
        st.info("Start the API with `uvicorn backend.app.main:app --reload`.")
        st.stop()
    return data


def level_bar(counts: dict, title: str, order=None):
    order = order or ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    rows = [(k, counts.get(k, 0)) for k in order if k in counts] or list(counts.items())
    df = pd.DataFrame(rows, columns=["level", "count"])
    fig = px.bar(
        df, x="level", y="count", color="level", title=title,
        color_discrete_map=LEVEL_COLORS, text="count",
    )
    fig.update_layout(showlegend=False, height=360)
    return fig


def api_post(path: str, payload: dict):
    """POST JSON to the API. Returns (data, error_message)."""
    try:
        resp = requests.post(f"{API_BASE}{path}", json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as exc:
        return None, str(exc)


def render_ai_response(resp: dict):
    """Render a structured AI analyst response (answer + evidence)."""
    st.markdown(f"#### Answer\n{resp.get('answer', '')}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Intent", resp.get("intent", "?"))
    c2.metric("Confidence", resp.get("confidence", 0))
    c3.metric("Generator", resp.get("generator", "?"))
    if resp.get("resolved_from_context"):
        st.caption("↳ resolved using prior conversation context")
    if resp.get("risk_justification"):
        st.info(resp["risk_justification"])
    se = resp.get("supporting_entities") or []
    if se:
        st.markdown("**Supporting entities**")
        st.dataframe(pd.DataFrame(se), width="stretch", hide_index=True)
    rels = resp.get("graph_relationships") or []
    if rels:
        st.markdown("**Graph relationships**")
        for r in rels[:15]:
            st.write(f"• {r}")
    st.caption("Data sources: " + ", ".join(resp.get("data_sources", [])))
    with st.expander("Raw evidence (findings)"):
        st.json(resp.get("findings", {}))


# ── Sidebar navigation ──────────────────────────────────────
# PAGES stays the single source of truth for routing; ui.render_sidebar groups
# these names for display only. Any page missing from the nav groups is still
# reachable (ui.build_nav files it under "Other").
PAGES = [
    "Executive Overview",
    "Threat Intelligence Overview",
    "Risk Analysis",
    "ATT&CK Analysis",
    "CVE Analysis",
    "Correlation Explorer",
    "EPSS Analysis",
    "KEV Analysis",
    "Threat Prioritization",
    "SOC Readiness",
    "MISP Intelligence Overview",
    "Threat Actors",
    "Malware Analysis",
    "IOC Explorer",
    "Campaign Explorer",
    "Threat Intelligence Relationships",
    "SOC Overview",
    "Live Alerts",
    "Threat-Enriched Alerts",
    "Threat Actor Activity",
    "Malware Activity",
    "Campaign Activity",
    "Priority Queue",
    "Knowledge Graph Overview",
    "Threat Actor Graph",
    "Campaign Graph",
    "Alert Investigation Graph",
    "CVE Relationship Graph",
    "Graph Intelligence Center",
    "Attack Path Explorer",
    "Threat Actor Influence",
    "Campaign Communities",
    "High-Risk CVEs",
    "Graph-Based Risk Analysis",
    "AI Threat Analyst",
    "Investigation Assistant",
    "Attack Path Investigator",
    "Threat Actor Investigator",
    "AI Risk Advisor",
    "Agentic SOC Analyst",
    "Autonomous Investigations",
    "Blast Radius Explorer",
    "Risk Explanation Center",
    "Investigation Reports",
    "SOC Briefings",
    "CTI Reports",
    "Investigation History",
    "Autonomous Triage Center",
    "Predictive Intelligence Center",
    "Predicted Threat Actors",
    "Predicted CVEs",
    "Emerging Campaigns",
    "Graph Embedding Explorer",
    "ATT&CK Coverage Center",
    "Detection Gap Explorer",
    "Coverage Heatmaps",
    "Coverage Trends",
    "Detection Engineering Advisor",
    "Pipeline Operations Center",
    "Scheduler Dashboard",
    "Pipeline History",
    "Job Monitoring",
    "Autonomous Operations Center",
    "SOAR Integration Center",
    "Response Recommendations",
    "Approval Queue",
    "Action Execution Center",
    "Response Audit Trail",
    "SOAR Response Center",
]
page = ui.render_sidebar(PAGES, API_BASE)


# ── Page 1: Executive Overview ──────────────────────────────
def executive_overview():
    tech = require("/stats/techniques")
    cve = require("/stats/cves")
    corr = require("/stats/correlations")
    risk = require("/stats/risk-scores")
    epss = require("/stats/epss")
    kev = require("/stats/kev")
    prio = require("/stats/priority")

    latest = (cve.get("latest_published") or "")[:10]
    ui.page_header(
        "Executive Overview",
        subtitle=(f"Latest CVE published {latest}" if latest else ""),
        eyebrow="Threat posture",
    )

    ui.section("Intelligence corpus")
    ui.kpi_row([
        {"label": "ATT&CK Techniques", "value": f"{tech['total']:,}",
         "hint": f"{tech['parent_techniques']:,} parent · "
                 f"{tech['sub_techniques']:,} sub"},
        {"label": "CVEs", "value": f"{cve['total']:,}"},
        {"label": "Correlations", "value": f"{corr['total_correlations']:,}"},
        {"label": "Risk Scores", "value": f"{risk['total']:,}"},
    ])

    ui.section("Exploitation signals")
    ui.kpi_row([
        {"label": "EPSS Scored", "value": f"{epss['total']:,}"},
        {"label": "KEV Entries", "value": f"{kev['total']:,}"},
        {"label": "Prioritized CVEs", "value": f"{prio['total']:,}"},
        {"label": "KEV in Priority", "value": f"{prio['kev_count']:,}",
         "accent": True},
    ])

    ui.section("Severity distribution", "CVEs by CVSS severity")
    ui.level_pills(cve.get("by_severity", {}))

    ui.section("Exposure")
    ui.kpi_row([
        {"label": "Critical CVEs mapped to ATT&CK",
         "value": f"{corr['critical_cves_mapped']:,}", "accent": True},
        {"label": "Avg. CVSS", "value": cve.get("average_cvss") or "n/a"},
        {"label": "Avg. Priority", "value": prio.get("average_score") or "n/a"},
    ])

    ui.section("Priority and risk breakdown")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(level_bar(prio.get("by_level", {}),
                                  "CVEs by threat priority"), width="stretch")
    with c2:
        st.plotly_chart(level_bar(risk.get("by_level", {}),
                                  "CVEs by risk level"), width="stretch")


# ── Page 2: Threat Intelligence Overview ────────────────────
def ti_overview():
    ui.page_header("Threat Intelligence Overview")
    tech = require("/stats/techniques")
    cve = require("/stats/cves")
    corr = require("/stats/correlations")

    st.subheader("ATT&CK")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total techniques", f"{tech['total']:,}")
    c2.metric("Parent techniques", f"{tech['parent_techniques']:,}")
    c3.metric("Sub-techniques", f"{tech['sub_techniques']:,}")

    st.subheader("CVEs")
    c1, c2 = st.columns(2)
    c1.plotly_chart(
        level_bar(cve.get("by_severity", {}), "CVEs by severity"),
        width="stretch",
    )
    with c2:
        st.metric("Total CVEs", f"{cve['total']:,}")
        st.metric("Average CVSS", cve.get("average_cvss") or "n/a")
        st.metric("Latest published", (cve.get("latest_published") or "n/a")[:10])

    st.subheader("Correlations")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total correlations", f"{corr['total_correlations']:,}")
    c2.metric("Distinct techniques", f"{corr['distinct_techniques']:,}")
    c3.metric("Distinct CVEs", f"{corr['distinct_cves']:,}")
    st.plotly_chart(
        level_bar(corr.get("by_confidence_level", {}), "Correlations by confidence",
                  order=["HIGH", "MEDIUM", "LOW"]),
        width="stretch",
    )


# ── Page 3: Risk Analysis ───────────────────────────────────
def risk_analysis():
    ui.page_header("Risk Analysis")
    risk = require("/stats/risk-scores")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Scored CVEs", f"{risk['total']:,}")
    c2.metric("Average", risk.get("average_score") or "n/a")
    c3.metric("Max", risk.get("max_score") or "n/a")
    c4.metric("Model", risk.get("model_version") or "n/a")

    c1, c2 = st.columns(2)
    dist = risk.get("distribution", {})
    df = pd.DataFrame(list(dist.items()), columns=["bucket", "count"])
    fig = px.bar(df, x="bucket", y="count", title="Risk score distribution (0-100)",
                 text="count")
    fig.update_layout(height=360)
    c1.plotly_chart(fig, width="stretch")
    c2.plotly_chart(level_bar(risk.get("by_level", {}), "By risk level"),
                    width="stretch")

    st.subheader("Top critical risks")
    crit = require("/risk-scores/top", {"limit": 15, "risk_level": "CRITICAL"})
    if crit:
        st.dataframe(pd.DataFrame(crit)[
            ["cve_id", "risk_score", "risk_level", "severity", "cvss_score"]
        ], width="stretch", hide_index=True)
    else:
        st.info("No CRITICAL risk scores.")

    st.subheader("Top high-risk CVEs")
    top = require("/risk-scores/top", {"limit": 20})
    st.dataframe(pd.DataFrame(top)[
        ["cve_id", "risk_score", "risk_level", "severity", "cvss_score"]
    ], width="stretch", hide_index=True)


# ── Page 4: ATT&CK Analysis ─────────────────────────────────
def attack_analysis():
    ui.page_header("ATT&CK Analysis")
    corr = require("/stats/correlations", {"top": 15})

    st.subheader("Most associated techniques")
    techs = corr.get("most_associated_techniques", [])
    if techs:
        df = pd.DataFrame(techs)
        df["label"] = df["technique_id"] + " - " + df["name"].fillna("")
        fig = px.bar(df, x="correlation_count", y="label", orientation="h",
                     title="Techniques by correlation count")
        fig.update_layout(height=500, yaxis={"categoryorder": "total ascending"},
                          yaxis_title="", xaxis_title="correlations")
        st.plotly_chart(fig, width="stretch")

    st.subheader("Tactic breakdown")
    by_tactic = corr.get("by_tactic", {})
    if by_tactic:
        df = pd.DataFrame(sorted(by_tactic.items(), key=lambda kv: kv[1], reverse=True),
                          columns=["tactic", "count"])
        fig = px.pie(df, names="tactic", values="count", title="Correlations by ATT&CK tactic")
        fig.update_layout(height=420)
        st.plotly_chart(fig, width="stretch")

    st.subheader("Technique correlation ranking")
    if techs:
        st.dataframe(pd.DataFrame(techs)[
            ["technique_id", "name", "correlation_count"]
        ], width="stretch", hide_index=True)


# ── Page 5: CVE Analysis ────────────────────────────────────
def cve_analysis():
    ui.page_header("CVE Analysis")
    cve = require("/stats/cves")

    c1, c2 = st.columns(2)
    c1.plotly_chart(level_bar(cve.get("by_severity", {}), "Severity distribution"),
                    width="stretch")
    cvss_dist = cve.get("cvss_distribution", {})
    if cvss_dist:
        df = pd.DataFrame(list(cvss_dist.items()), columns=["range", "count"])
        fig = px.bar(df, x="range", y="count", title="CVSS distribution", text="count")
        fig.update_layout(height=360)
        c2.plotly_chart(fig, width="stretch")

    st.subheader("Critical vulnerability analysis")
    crit = require("/cves", {"severity": "CRITICAL", "limit": 50})
    st.caption(f"Showing up to 50 of the most recent CRITICAL CVEs.")
    if crit:
        df = pd.DataFrame(crit)[["cve_id", "cvss_score", "severity", "published_date", "description"]]
        df["published_date"] = df["published_date"].astype(str).str[:10]
        df["description"] = df["description"].str.slice(0, 120) + "..."
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("No CRITICAL CVEs.")


# ── Page 6: Correlation Explorer ────────────────────────────
def correlation_explorer():
    ui.page_header("Correlation Explorer")
    c1, c2, c3, c4 = st.columns(4)
    level = c1.selectbox("Confidence", ["Any", "HIGH", "MEDIUM", "LOW"])
    severity = c2.selectbox("CVE severity", ["Any", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
    min_conf = c3.slider("Min confidence", 0.0, 1.0, 0.0, 0.05)
    search = c4.text_input("Search (technique / CVE / keyword)")

    params = {"limit": 200, "min_confidence": min_conf}
    if level != "Any":
        params["confidence_level"] = level
    if severity != "Any":
        params["severity"] = severity
    if search:
        params["search"] = search

    rows = require("/correlations", params)
    st.caption(f"{len(rows)} correlations (capped at 200).")
    if rows:
        df = pd.DataFrame(rows)
        df["matched_keywords"] = df["matched_keywords"].apply(
            lambda ks: ", ".join(ks) if isinstance(ks, list) else ks
        )
        st.dataframe(
            df[[
                "technique_id", "technique_name", "tactic", "cve_id", "severity",
                "cvss_score", "confidence_score", "confidence_level", "matched_keywords",
            ]],
            width="stretch", hide_index=True,
        )
    else:
        st.info("No correlations match these filters.")


# ── Page 7: EPSS Analysis ───────────────────────────────────
def epss_analysis():
    ui.page_header("EPSS Analysis")
    stats = require("/stats/epss")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CVEs scored", f"{stats['total']:,}")
    c2.metric("Avg EPSS", stats.get("average_score") or "n/a")
    c3.metric("EPSS ≥ 0.5", f"{stats['above_0_5']:,}")
    c4.metric("EPSS ≥ 0.1", f"{stats['above_0_1']:,}")
    st.caption(f"EPSS model date: {stats.get('score_date') or 'n/a'} "
               f"({stats.get('model_version') or 'n/a'})")

    dist = stats.get("distribution", {})
    df = pd.DataFrame(list(dist.items()), columns=["probability", "count"])
    fig = px.bar(df, x="probability", y="count", title="EPSS probability distribution",
                 text="count", log_y=True)
    fig.update_layout(height=360)
    st.plotly_chart(fig, width="stretch")

    st.subheader("Top EPSS vulnerabilities (most likely to be exploited)")
    top = require("/epss/top", {"limit": 20})
    if top:
        st.dataframe(pd.DataFrame(top)[
            ["cve_id", "epss_score", "percentile", "severity", "cvss_score"]
        ], width="stretch", hide_index=True)

    st.subheader("EPSS vs CVSS")
    sample = require("/epss", {"limit": 500, "min_score": 0.0})
    if sample:
        df = pd.DataFrame(sample)
        df = df[df["cvss_score"].notna()]
        fig = px.scatter(
            df, x="cvss_score", y="epss_score", color="severity",
            color_discrete_map=LEVEL_COLORS, hover_data=["cve_id"],
            title="Exploit probability (EPSS) vs technical severity (CVSS)",
            labels={"cvss_score": "CVSS", "epss_score": "EPSS"},
        )
        fig.update_layout(height=420)
        st.plotly_chart(fig, width="stretch")
        st.caption("High CVSS does not imply high exploit likelihood - the bottom-right "
                   "shows severe-but-unlikely CVEs that raw CVSS would over-prioritize.")


# ── Page 8: KEV Analysis ────────────────────────────────────
def kev_analysis():
    ui.page_header("CISA KEV Analysis")
    stats = require("/stats/kev")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("KEV entries", f"{stats['total']:,}")
    c2.metric("Ransomware-linked", f"{stats['known_ransomware']:,}")
    c3.metric("In our catalog", f"{stats['in_local_catalog']:,}")
    c4.metric("Latest batch", f"{stats['recent_additions']:,}")

    st.subheader("Top vendors in KEV")
    vendors = stats.get("top_vendors", {})
    if vendors:
        df = pd.DataFrame(sorted(vendors.items(), key=lambda kv: kv[1], reverse=True),
                          columns=["vendor", "count"])
        fig = px.bar(df, x="count", y="vendor", orientation="h", title="KEV entries by vendor")
        fig.update_layout(height=420, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, width="stretch")

    st.subheader("KEV vulnerabilities in our catalog (with ATT&CK mappings)")
    rows = require("/kev/in-catalog", {"limit": 100})
    if rows:
        df = pd.DataFrame(rows)[
            ["cve_id", "vendor_project", "product", "severity", "cvss_score",
             "known_ransomware", "date_added"]
        ]
        st.dataframe(df, width="stretch", hide_index=True)
        # KEV severity breakdown for the actionable set.
        sev_counts = df["severity"].fillna("UNSCORED").value_counts().to_dict()
        st.plotly_chart(level_bar(sev_counts, "Severity of KEV CVEs we track",
                                  order=["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNSCORED"]),
                        width="stretch")
    else:
        st.info("None of our tracked CVEs are currently in the KEV catalog.")


# ── Page 9: Threat Prioritization ───────────────────────────
def threat_prioritization():
    ui.page_header("Threat Prioritization")
    stats = require("/stats/priority")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Prioritized CVEs", f"{stats['total']:,}")
    c2.metric("KEV-listed", f"{stats['kev_count']:,}")
    c3.metric("Avg priority", stats.get("average_score") or "n/a")
    c4.metric("Avg ML risk (old)", stats.get("average_ml_risk") or "n/a")
    st.caption(f"{stats['escalated_by_kev']} CVEs escalated by KEV vs the ML-only score "
               "— real-world exploitation evidence overriding the model.")

    c1, c2 = st.columns(2)
    c1.plotly_chart(level_bar(stats.get("by_level", {}), "Priority levels"), width="stretch")
    dist = stats.get("distribution", {})
    df = pd.DataFrame(list(dist.items()), columns=["bucket", "count"])
    fig = px.bar(df, x="bucket", y="count", title="Priority score distribution", text="count")
    fig.update_layout(height=360)
    c2.plotly_chart(fig, width="stretch")

    st.subheader("🚨 Top vulnerabilities to patch")
    top = require("/priority/top", {"limit": 20})
    if top:
        df = pd.DataFrame(top)
        df["kev"] = df["kev_flag"].map({True: "✓", False: ""})
        st.dataframe(
            df[["cve_id", "priority_score", "priority_level", "kev", "epss_score",
                "ml_risk_score", "severity", "cvss_score"]],
            width="stretch", hide_index=True,
        )

    st.subheader("Why? Priority score breakdown")
    cve_id = st.text_input("Enter a CVE ID for its explanation", value=top[0]["cve_id"] if top else "")
    if cve_id:
        data, err = api_get(f"/priority/{cve_id.strip()}/explanation")
        if err or data is None:
            st.warning(f"No priority score found for {cve_id}.")
        else:
            st.markdown(f"**{data['cve_id']}** — priority **{data['priority_score']}** "
                        f"({data['priority_level']})")
            st.info(data.get("explanation") or "")
            comp = data.get("components", {})
            cdf = pd.DataFrame(sorted(comp.items(), key=lambda kv: kv[1], reverse=True),
                               columns=["component", "points"])
            fig = px.bar(cdf, x="points", y="component", orientation="h",
                         title="Points contributed by each signal")
            fig.update_layout(height=320, yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, width="stretch")


# ── Page 10: SOC Readiness ──────────────────────────────────
def soc_readiness():
    ui.page_header("SOC Readiness — Wazuh Enrichment Demo")
    st.caption("Demonstrates how a future Wazuh alert would be auto-enriched with "
               "ATT&CK, CVE, EPSS, KEV, and priority intelligence. No live Wazuh "
               "instance is connected in this phase.")

    alert = require("/soc/demo-alert")

    st.subheader("Simulated Wazuh alert")
    c1, c2, c3 = st.columns(3)
    c1.metric("Rule ID", alert.get("rule_id") or "n/a")
    c2.metric("Agent", alert.get("agent_name") or "n/a")
    c3.metric("Top priority", alert.get("highest_priority_score") or "n/a")
    st.success(f"**Recommended action:** {alert['recommended_action']}")

    for enr in alert.get("enrichments", []):
        with st.expander(f"🔎 {enr['summary']}", expanded=True):
            if not enr["found"]:
                st.warning("CVE not in local catalog.")
                continue
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**CVE**")
                st.write(f"Severity: {enr.get('severity')}")
                st.write(f"CVSS: {enr.get('cvss_score')}")
            with c2:
                st.markdown("**EPSS / KEV**")
                st.write(f"EPSS: {enr['epss']['epss_score'] if enr.get('epss') else 'n/a'}")
                kev = enr.get("kev") or {}
                st.write(f"In KEV: {'✓' if kev.get('in_kev') else '✗'}")
                if kev.get("in_kev"):
                    st.write(f"Due: {kev.get('due_date') or 'n/a'}")
            with c3:
                st.markdown("**Priority**")
                pr = enr.get("priority") or {}
                st.write(f"Score: {pr.get('priority_score')}")
                st.write(f"Level: {pr.get('priority_level')}")
            techs = enr.get("attack_techniques", [])
            if techs:
                st.markdown("**Mapped ATT&CK techniques**")
                st.dataframe(pd.DataFrame(techs)[
                    ["technique_id", "name", "tactic", "confidence_score", "confidence_level"]
                ], width="stretch", hide_index=True)
            if enr.get("priority", {}).get("explanation"):
                st.info(enr["priority"]["explanation"])


# ── Page 11: MISP Intelligence Overview ─────────────────────
def misp_overview():
    ui.page_header("MISP Intelligence Overview")
    s = require("/stats/misp")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Events", f"{s['events']:,}")
    c2.metric("IOCs", f"{s['iocs']:,}")
    c3.metric("Threat Actors", f"{s['threat_actors']:,}")
    c4.metric("Malware Families", f"{s['malware_families']:,}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Campaigns", f"{s['campaigns']:,}")
    c2.metric("Relationships", f"{s['relationships']:,}")
    c3.metric("Published Events", f"{s['published_events']:,}")

    c1, c2 = st.columns(2)
    ioc_types = s.get("ioc_types", {})
    if ioc_types:
        df = pd.DataFrame(sorted(ioc_types.items(), key=lambda kv: kv[1], reverse=True),
                          columns=["type", "count"])
        c1.plotly_chart(px.bar(df, x="count", y="type", orientation="h",
                               title="IOC types").update_layout(height=380,
                               yaxis={"categoryorder": "total ascending"}),
                        width="stretch")
    by_level = s.get("events_by_threat_level", {})
    if by_level:
        df = pd.DataFrame(list(by_level.items()), columns=["threat_level", "count"])
        c2.plotly_chart(px.pie(df, names="threat_level", values="count",
                               title="Events by threat level").update_layout(height=380),
                        width="stretch")


# ── Page 12: Threat Actors ──────────────────────────────────
def threat_actors_page():
    ui.page_header("Threat Actors")
    s = require("/stats/misp")
    top = s.get("top_actors_by_relationships", [])
    if top:
        df = pd.DataFrame(top)
        st.plotly_chart(px.bar(df, x="relationships", y="name", orientation="h",
                               title="Top threat actors by relationships").update_layout(
                               height=360, yaxis={"categoryorder": "total ascending"}),
                        width="stretch")

    actors = require("/actors", {"limit": 200})
    if not actors:
        st.info("No threat actors ingested. Run `python -m collectors.misp --sample ...`.")
        return
    names = {a["actor_name"]: a["id"] for a in actors}
    chosen = st.selectbox("Inspect an actor", list(names))
    detail = require(f"/actors/{names[chosen]}")
    st.caption(detail.get("description") or "")
    c1, c2, c3 = st.columns(3)
    c1.metric("Techniques", len(detail.get("techniques", [])))
    c2.metric("CVEs exploited", len(detail.get("cves", [])))
    c3.metric("Malware used", len(detail.get("malware", [])))
    if detail.get("techniques"):
        st.markdown("**ATT&CK techniques (with evidence)**")
        st.dataframe(pd.DataFrame(detail["techniques"])[
            ["target_key", "confidence", "explanation"]
        ].rename(columns={"target_key": "technique"}), width="stretch", hide_index=True)
    if detail.get("cves"):
        st.markdown("**Top exploited CVEs**")
        st.dataframe(pd.DataFrame(detail["cves"])[
            ["target_key", "confidence", "explanation"]
        ].rename(columns={"target_key": "cve"}).head(25), width="stretch", hide_index=True)


# ── Page 13: Malware Analysis ───────────────────────────────
def malware_page():
    ui.page_header("Malware Analysis")
    s = require("/stats/misp")
    top = s.get("top_malware_by_relationships", [])
    if top:
        df = pd.DataFrame(top)
        st.plotly_chart(px.bar(df, x="relationships", y="name", orientation="h",
                               title="Top malware families by relationships").update_layout(
                               height=360, yaxis={"categoryorder": "total ascending"}),
                        width="stretch")
    malware = require("/malware", {"limit": 200})
    if not malware:
        st.info("No malware families ingested.")
        return
    names = {m["malware_name"]: m["id"] for m in malware}
    chosen = st.selectbox("Inspect malware", list(names))
    detail = require(f"/malware/{names[chosen]}")
    st.caption(detail.get("description") or "")
    if detail.get("techniques"):
        st.markdown("**ATT&CK techniques**")
        st.dataframe(pd.DataFrame(detail["techniques"])[
            ["target_key", "confidence", "explanation"]
        ].rename(columns={"target_key": "technique"}), width="stretch", hide_index=True)


# ── Page 14: IOC Explorer ───────────────────────────────────
def ioc_explorer():
    ui.page_header("IOC Explorer")
    c1, c2 = st.columns(2)
    ioc_type = c1.text_input("Filter by type (e.g. domain, ip-dst, md5)")
    search = c2.text_input("Search value")
    params = {"limit": 300}
    if ioc_type:
        params["type"] = ioc_type
    if search:
        params["search"] = search
    iocs = require("/iocs", params)
    st.caption(f"{len(iocs)} IOCs (capped at 300).")
    if iocs:
        st.dataframe(pd.DataFrame(iocs)[
            ["misp_attribute_id", "type", "value", "category", "to_ids", "misp_event_id"]
        ], width="stretch", hide_index=True)
        types = pd.DataFrame(iocs)["type"].value_counts().reset_index()
        types.columns = ["type", "count"]
        st.plotly_chart(px.bar(types, x="type", y="count", title="IOC type distribution")
                        .update_layout(height=320), width="stretch")


# ── Page 15: Campaign Explorer ──────────────────────────────
def campaign_explorer():
    ui.page_header("Campaign Explorer")
    campaigns = require("/campaigns", {"limit": 200})
    if not campaigns:
        st.info("No campaigns ingested.")
        return
    st.dataframe(pd.DataFrame(campaigns)[
        ["campaign_name", "source", "description"]
    ], width="stretch", hide_index=True)
    st.metric("Total campaigns", len(campaigns))


# ── Page 16: Threat Intelligence Relationships ──────────────
def ti_relationships():
    ui.page_header("Threat Intelligence Relationships")
    s = require("/stats/misp")
    st.metric("Total relationship edges", f"{s['relationships']:,}")
    # Per-actor relationship counts as a proxy for the enrichment graph density.
    actors = require("/actors", {"limit": 200})
    rows = []
    for a in actors[:15]:
        d = require(f"/actors/{a['id']}")
        rows.append({
            "actor": a["actor_name"],
            "techniques": len(d.get("techniques", [])),
            "cves": len(d.get("cves", [])),
            "malware": len(d.get("malware", [])),
        })
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, width="stretch", hide_index=True)
        melted = df.melt(id_vars="actor", var_name="relationship", value_name="count")
        st.plotly_chart(px.bar(melted, x="actor", y="count", color="relationship",
                               title="Relationship counts by actor", barmode="group")
                        .update_layout(height=400), width="stretch")


# ── Phase 10: Wazuh SOC pages ───────────────────────────────
def _alert_level_palette(counts: dict, title: str):
    df = pd.DataFrame(sorted(counts.items(), key=lambda kv: int(kv[0]) if str(kv[0]).isdigit() else 0),
                      columns=["level", "count"])
    fig = px.bar(df, x="level", y="count", title=title, text="count")
    fig.update_layout(height=340)
    return fig


def soc_overview():
    ui.page_header("SOC Overview")
    s = require("/wazuh/stats")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Agents", f"{s['agents']:,}", f"{s['agents_active']} active")
    c2.metric("Alerts", f"{s['alerts']:,}")
    c3.metric("Enriched alerts", f"{s['enriched_alerts']:,}")
    c4.metric("KEV-linked alerts", f"{s['kev_linked_alerts']:,}")

    c1, c2 = st.columns(2)
    if s.get("alerts_by_level"):
        c1.plotly_chart(_alert_level_palette(s["alerts_by_level"], "Alerts by Wazuh severity (rule level)"),
                        width="stretch")
    if s.get("alerts_by_priority"):
        c2.plotly_chart(level_bar(s["alerts_by_priority"], "Alerts by SOC priority"), width="stretch")

    st.subheader("Most targeted ATT&CK techniques")
    if s.get("top_techniques"):
        df = pd.DataFrame(s["top_techniques"])
        fig = px.bar(df, x="count", y="technique_id", orientation="h", title="Alerts per technique")
        fig.update_layout(height=380, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, width="stretch")


def live_alerts():
    ui.page_header("Live Alerts")
    c1, c2, c3 = st.columns(3)
    min_level = c1.slider("Min Wazuh level", 0, 15, 0)
    agent = c2.text_input("Agent ID")
    search = c3.text_input("Search description")
    params = {"limit": 200, "min_level": min_level}
    if agent:
        params["agent_id"] = agent
    if search:
        params["search"] = search
    rows = require("/wazuh/alerts", params)
    st.caption(f"{len(rows)} alerts (cap 200). Wazuh severity is shown unchanged.")
    if rows:
        df = pd.DataFrame(rows)
        df["techniques"] = df["mitre_techniques"].apply(
            lambda t: ", ".join(t) if isinstance(t, list) else "")
        st.dataframe(df[["timestamp", "agent_id", "rule_id", "rule_level",
                         "description", "techniques"]], width="stretch", hide_index=True)


def threat_enriched_alerts():
    ui.page_header("Threat-Enriched Alerts")
    c1, c2, c3 = st.columns(3)
    level = c1.selectbox("Priority", ["Any", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
    kev = c2.checkbox("KEV-linked only")
    actor = c3.checkbox("Attributed to actor only")
    params = {"limit": 100}
    if level != "Any":
        params["priority_level"] = level
    if kev:
        params["kev_only"] = True
    if actor:
        params["actor_only"] = True
    rows = require("/wazuh/enriched-alerts", params)
    st.caption(f"{len(rows)} enriched alerts.")
    for a in rows[:40]:
        enr = a.get("enrichment") or {}
        title = (f"[{enr.get('priority_level','?')} {enr.get('priority_score','?')}] "
                 f"{a.get('description','')[:80]}")
        with st.expander(title):
            ev = enr.get("evidence") or {}
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Agent:** {a.get('agent_id')}")
            c1.write(f"**Wazuh level:** {a.get('rule_level')}")
            c2.write(f"**KEV:** {'yes' if enr.get('kev_present') else 'no'}")
            c2.write(f"**EPSS:** {enr.get('epss_score')}")
            c3.write(f"**Existing risk:** {enr.get('existing_risk_score')}")
            c3.write(f"**Confidence:** {enr.get('confidence_score')}")
            st.write(f"**Techniques:** {', '.join(ev.get('techniques', []))}")
            st.write(f"**Related CVEs:** {ev.get('cve_count', 0)} | "
                     f"**Actors:** {', '.join(ev.get('threat_actors', [])) or 'none'} | "
                     f"**Malware:** {', '.join(ev.get('malware', [])) or 'none'}")
            if ev.get("rationale"):
                st.info(ev["rationale"])


def _alerts_grouped_by(field_path):
    """Aggregate enriched alerts by an evidence field client-side."""
    rows = require("/wazuh/enriched-alerts", {"limit": 500})
    counts = defaultdict(int)
    for a in rows:
        ev = (a.get("enrichment") or {}).get("evidence") or {}
        for val in ev.get(field_path, []):
            counts[val] += 1
    return counts, rows


def threat_actor_activity():
    ui.page_header("Threat Actor Activity")
    counts, _ = _alerts_grouped_by("threat_actors")
    if counts:
        df = pd.DataFrame(sorted(counts.items(), key=lambda kv: kv[1], reverse=True),
                          columns=["actor", "alerts"])
        fig = px.bar(df, x="alerts", y="actor", orientation="h",
                     title="Alerts attributed to threat actors")
        fig.update_layout(height=420, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, width="stretch")
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("No actor-attributed alerts yet.")


def malware_activity():
    ui.page_header("Malware Activity")
    counts, _ = _alerts_grouped_by("malware")
    if counts:
        df = pd.DataFrame(sorted(counts.items(), key=lambda kv: kv[1], reverse=True),
                          columns=["malware", "alerts"])
        fig = px.bar(df, x="alerts", y="malware", orientation="h", title="Alerts linked to malware")
        fig.update_layout(height=420, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, width="stretch")
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("No malware-linked alerts yet.")


def campaign_activity():
    ui.page_header("Campaign Activity")
    counts, _ = _alerts_grouped_by("campaigns")
    if counts:
        df = pd.DataFrame(sorted(counts.items(), key=lambda kv: kv[1], reverse=True),
                          columns=["campaign", "alerts"])
        fig = px.pie(df, names="campaign", values="alerts", title="Alerts by campaign")
        st.plotly_chart(fig, width="stretch")
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("No campaign-linked alerts yet.")


def priority_queue():
    ui.page_header("Priority Queue")
    st.caption("Highest-priority alerts to work first (SOC priority, not Wazuh severity).")
    rows = require("/wazuh/enriched-alerts", {"limit": 50})
    if not rows:
        st.info("No enriched alerts.")
        return
    recs = []
    for a in rows:
        enr = a.get("enrichment") or {}
        recs.append({
            "priority": enr.get("priority_score"),
            "level": enr.get("priority_level"),
            "alert": a.get("description"),
            "agent": a.get("agent_id"),
            "wazuh_level": a.get("rule_level"),
            "kev": "✓" if enr.get("kev_present") else "",
            "epss": enr.get("epss_score"),
            "risk": enr.get("existing_risk_score"),
        })
    df = pd.DataFrame(recs).sort_values("priority", ascending=False)
    st.dataframe(df, width="stretch", hide_index=True)


# ── Phase 11: Knowledge Graph pages ─────────────────────────
_GRAPH_COLORS = {
    "Technique": "#6366f1", "CVE": "#ef4444", "ThreatActor": "#b91c1c",
    "Malware": "#d97706", "Campaign": "#0891b2", "IOC": "#16a34a",
    "Agent": "#7c3aed", "Alert": "#db2777", "RiskScore": "#64748b",
}


def _graph_layout(nodes):
    """Deterministic clustered layout (group by label) - no networkx needed."""
    groups = defaultdict(list)
    for n in nodes:
        groups[n["label"]].append(n)
    labels = sorted(groups)
    pos = {}
    for li, lab in enumerate(labels):
        cx = math.cos(2 * math.pi * li / max(len(labels), 1)) * 3.0
        cy = math.sin(2 * math.pi * li / max(len(labels), 1)) * 3.0
        g = groups[lab]
        for i, n in enumerate(g):
            ang = 2 * math.pi * i / max(len(g), 1)
            r = 0.5 + 1.1 * (i / max(len(g), 1))
            pos[n["id"]] = (cx + r * math.cos(ang), cy + r * math.sin(ang))
    return pos


def render_network(payload, title, max_nodes=200):
    nodes = payload.get("nodes", [])[:max_nodes]
    node_ids = {n["id"] for n in nodes}
    edges = [e for e in payload.get("edges", [])
             if e["source"] in node_ids and e["target"] in node_ids]
    if not nodes:
        st.info("No graph data for this entity.")
        return
    pos = _graph_layout(nodes)

    edge_x, edge_y = [], []
    for e in edges:
        x0, y0 = pos[e["source"]]
        x1, y1 = pos[e["target"]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines",
                             line=dict(width=0.6, color="#cbd5e1"), hoverinfo="none"))
    by_label = defaultdict(lambda: {"x": [], "y": [], "text": []})
    for n in nodes:
        x, y = pos[n["id"]]
        by_label[n["label"]]["x"].append(x)
        by_label[n["label"]]["y"].append(y)
        by_label[n["label"]]["text"].append(n["name"])
    for label, d in by_label.items():
        fig.add_trace(go.Scatter(
            x=d["x"], y=d["y"], mode="markers", name=label,
            marker=dict(size=12, color=_GRAPH_COLORS.get(label, "#94a3b8")),
            text=d["text"], hovertemplate=f"{label}: %{{text}}<extra></extra>"))
    fig.update_layout(title=title, height=560, showlegend=True,
                      xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, width="stretch")


def knowledge_graph_overview():
    ui.page_header("Knowledge Graph Overview")
    stats = require("/graph/stats")
    c1, c2 = st.columns(2)
    c1.metric("Total nodes", f"{stats['total_nodes']:,}")
    c2.metric("Total relationships", f"{stats['total_relationships']:,}")

    c1, c2 = st.columns(2)
    nc = stats.get("node_counts", {})
    df = pd.DataFrame(sorted(nc.items(), key=lambda kv: kv[1], reverse=True), columns=["label", "count"])
    c1.plotly_chart(px.bar(df, x="count", y="label", orientation="h", title="Nodes by label")
                    .update_layout(height=380, yaxis={"categoryorder": "total ascending"}), width="stretch")
    rc = stats.get("relationship_counts", {})
    df2 = pd.DataFrame(sorted(rc.items(), key=lambda kv: kv[1], reverse=True), columns=["type", "count"])
    c2.plotly_chart(px.bar(df2, x="count", y="type", orientation="h", title="Relationships by type")
                    .update_layout(height=380, yaxis={"categoryorder": "total ascending"}), width="stretch")

    st.subheader("Most connected entities")
    top = require("/graph/top-entities", {"limit": 15})["entities"]
    if top:
        st.dataframe(pd.DataFrame(top), width="stretch", hide_index=True)


def threat_actor_graph():
    ui.page_header("Threat Actor Graph")
    actors = require("/actors", {"limit": 200})
    if not actors:
        st.info("No threat actors ingested.")
        return
    names = {f"{a['actor_name']} (#{a['id']})": a["id"] for a in actors}
    pick = st.selectbox("Threat actor", list(names))
    payload = require(f"/graph/actor/{names[pick]}")
    st.caption(f"Ecosystem: {payload.get('summary', {})}")
    render_network(payload, f"Threat actor ecosystem — {pick}")


def campaign_graph():
    ui.page_header("Campaign Graph")
    camps = require("/campaigns", {"limit": 200})
    if not camps:
        st.info("No campaigns ingested.")
        return
    names = {f"{c['campaign_name']} (#{c['id']})": c["id"] for c in camps}
    pick = st.selectbox("Campaign", list(names))
    data, err = api_get(f"/graph/campaign/{names[pick]}")
    if err or not data or not data.get("nodes"):
        st.info("No graph data for this campaign.")
        return
    st.caption(f"Ecosystem: {data.get('summary', {})}")
    render_network(data, f"Campaign ecosystem — {pick}")


def alert_investigation_graph():
    ui.page_header("Alert Investigation Graph")
    st.caption("Alert → Technique → CVE → Threat Actor → Malware/Campaign")
    alerts = require("/wazuh/enriched-alerts", {"limit": 50})
    if not alerts:
        st.info("No enriched alerts.")
        return
    labels = {f"[{(a.get('enrichment') or {}).get('priority_level','?')}] "
              f"{a.get('description','')[:60]} (#{a['id']})": a["id"] for a in alerts}
    pick = st.selectbox("Alert", list(labels))
    payload = require(f"/graph/alert/{labels[pick]}")
    st.caption(f"Investigation reach: {payload.get('summary', {})}")
    render_network(payload, f"Alert investigation — {pick[:50]}")


def cve_relationship_graph():
    ui.page_header("CVE Relationship Graph")
    st.caption("CVE → Techniques → Alerts and CVE → Threat Actors")
    cve = st.text_input("CVE ID", value="CVE-2024-3094")
    if cve:
        data, err = api_get(f"/graph/cve/{cve.strip()}")
        if err or not data or not data.get("nodes"):
            st.info(f"No graph data for {cve} (is it correlated to a technique?).")
            return
        st.caption(f"Relationships: {data.get('summary', {})}")
        render_network(data, f"CVE relationships — {cve}")


# ── Phase 12: Graph intelligence pages ──────────────────────
def graph_intelligence_center():
    ui.page_header("Graph Intelligence Center")
    stats = require("/graph/stats")
    c1, c2 = st.columns(2)
    c1.metric("Graph nodes", f"{stats['total_nodes']:,}")
    c2.metric("Graph relationships", f"{stats['total_relationships']:,}")

    sev = st.selectbox("Severity", ["Any", "CRITICAL", "HIGH", "MEDIUM", "INFO"])
    params = {"limit": 200}
    if sev != "Any":
        params["severity"] = sev
    insights = require("/graph/insights", params)
    st.caption(f"{len(insights)} graph insights")
    if insights:
        df = pd.DataFrame(insights)[["insight_type", "severity", "entity_type", "entity_id", "insight"]]
        st.dataframe(df, width="stretch", hide_index=True)
        counts = df["insight_type"].value_counts().reset_index()
        counts.columns = ["insight_type", "count"]
        st.plotly_chart(px.bar(counts, x="count", y="insight_type", orientation="h",
                               title="Insights by type").update_layout(height=360,
                               yaxis={"categoryorder": "total ascending"}), width="stretch")


def attack_path_explorer():
    ui.page_header("Attack Path Explorer")
    st.caption("Alert → Technique → CVE → Threat Actor → Malware/Campaign")
    alerts = require("/wazuh/enriched-alerts", {"limit": 50})
    if not alerts:
        st.info("No enriched alerts.")
        return
    labels = {f"[{(a.get('enrichment') or {}).get('priority_level','?')}] "
              f"{a.get('description','')[:55]} (#{a['id']})": a["id"] for a in alerts}
    pick = st.selectbox("Alert", list(labels))
    data = require("/graph/attack-paths", {"alert_id": labels[pick]})
    paths = data.get("paths", [])
    st.caption(f"{len(paths)} attack path(s) found")
    if paths:
        st.dataframe(pd.DataFrame(paths)[["path", "technique", "cve", "threat_actor"]],
                     width="stretch", hide_index=True)
        gdata = require(f"/graph/alert/{labels[pick]}")
        render_network(gdata, f"Attack-path graph — {pick[:45]}")
    else:
        st.info("This alert has no path to a threat actor in the graph.")


def threat_actor_influence():
    ui.page_header("Threat Actor Influence")
    actors = require("/graph/top-threat-actors", {"limit": 15})
    if actors:
        df = pd.DataFrame(actors)
        df["actor"] = df["entity_id"]
        st.plotly_chart(px.bar(df, x="pagerank", y="actor", orientation="h",
                               title="Threat actors by PageRank influence").update_layout(
                               height=420, yaxis={"categoryorder": "total ascending"}),
                        width="stretch")
        st.dataframe(df[["entity_id", "pagerank", "degree_centrality", "betweenness", "community_id"]],
                     width="stretch", hide_index=True)
        actors_db = require("/actors", {"limit": 200})
        idn = {str(a["id"]): a["actor_name"] for a in actors_db}
        top_id = actors[0]["entity_id"]
        st.subheader(f"Influence map — {idn.get(top_id, top_id)}")
        render_network(require(f"/graph/actor/{top_id}"), "Top actor ecosystem")


def campaign_communities():
    ui.page_header("Campaign Communities")
    comms = require("/graph/communities", {"limit": 20})
    if not comms:
        st.info("No communities computed yet.")
        return
    df = pd.DataFrame([{"community": c["community_id"], "size": c["size"],
                        "types": ", ".join(f"{k}:{v}" for k, v in c["by_type"].items())}
                       for c in comms])
    st.plotly_chart(px.bar(df.head(15), x="size", y="community", orientation="h",
                           title="Largest graph communities").update_layout(
                           height=420, yaxis={"categoryorder": "total ascending"}), width="stretch")
    st.dataframe(df, width="stretch", hide_index=True)


def high_risk_cves():
    ui.page_header("High-Risk CVEs (graph influence)")
    cves = require("/graph/top-cves", {"limit": 20})
    if cves:
        df = pd.DataFrame(cves)
        st.plotly_chart(px.bar(df, x="pagerank", y="entity_id", orientation="h",
                               title="CVEs by graph PageRank").update_layout(
                               height=460, yaxis={"categoryorder": "total ascending"}), width="stretch")
        st.dataframe(df[["entity_id", "pagerank", "degree_centrality", "betweenness", "community_id"]],
                     width="stretch", hide_index=True)


def graph_based_risk_analysis():
    ui.page_header("Graph-Based Risk Analysis")
    rs = require("/stats/risk-scores")
    c1, c2, c3 = st.columns(3)
    c1.metric("Risk model", rs.get("model_version") or "n/a")
    c2.metric("Scored CVEs", f"{rs['total']:,}")
    c3.metric("Avg risk", rs.get("average_score") or "n/a")
    st.caption("ML Risk Scoring V5 incorporates graph-topology features "
               "(CVE PageRank/degree, actor influence, community risk, alert proximity).")
    st.plotly_chart(level_bar(rs.get("by_level", {}), "Risk levels (V5)"), width="stretch")

    st.subheader("Highest graph-influence entities (PageRank + betweenness)")
    hr = require("/graph/high-risk-entities", {"limit": 20})
    if hr:
        st.dataframe(pd.DataFrame(hr)[["entity_type", "entity_id", "pagerank",
                     "betweenness", "degree_centrality", "community_id"]],
                     width="stretch", hide_index=True)


# ── Phase 13: AI Threat Analyst pages ───────────────────────
def ai_threat_analyst():
    ui.page_header("🤖 AI Threat Analyst")
    st.caption("Ask natural-language investigation questions. Answers are grounded "
               "in real platform evidence (no hallucinated intelligence).")
    st.session_state.setdefault("ai_session", "dashboard-session")
    st.session_state.setdefault("ai_history", [])

    examples = [
        "Which threat actors are associated with my recent alerts?",
        "What are the most dangerous CVEs in my environment?",
        "Which MITRE techniques are most frequently observed?",
        "Which actors are associated with KEV vulnerabilities?",
        "Which alerts should analysts investigate first?",
    ]
    cols = st.columns(len(examples))
    picked = None
    for col, ex in zip(cols, examples):
        if col.button(ex[:18] + "…", help=ex):
            picked = ex
    question = st.text_input("Your question", value=picked or "")
    if st.button("Ask", type="primary") or picked:
        q = picked or question
        if q.strip():
            resp, err = api_post("/ai/query", {"question": q, "session_id": st.session_state.ai_session})
            if err:
                st.error(f"AI query failed: {err}")
            else:
                st.session_state.ai_history.insert(0, resp)
    for resp in st.session_state.ai_history[:5]:
        st.divider()
        st.markdown(f"**Q: {resp.get('question','')}**")
        render_ai_response(resp)


def investigation_assistant():
    ui.page_header("Investigation Assistant")
    kind = st.selectbox("Investigate", ["CVE", "Alert", "Threat Actor", "Campaign"])
    resp = err = None
    if kind == "CVE":
        cve = st.text_input("CVE ID", value="CVE-2024-3094")
        if st.button("Investigate") and cve:
            resp, err = api_post("/ai/investigate/cve", {"cve_id": cve.strip()})
    elif kind == "Alert":
        alerts = require("/wazuh/enriched-alerts", {"limit": 50})
        if alerts:
            labels = {f"#{a['id']} {a.get('description','')[:50]}": a["id"] for a in alerts}
            pick = st.selectbox("Alert", list(labels))
            if st.button("Investigate"):
                resp, err = api_post("/ai/investigate/alert", {"alert_id": labels[pick]})
    elif kind == "Threat Actor":
        actors = require("/actors", {"limit": 200})
        if actors:
            labels = {f"{a['actor_name']} (#{a['id']})": (a["id"], a["actor_name"]) for a in actors}
            pick = st.selectbox("Actor", list(labels))
            if st.button("Investigate"):
                resp, err = api_post("/ai/investigate/actor",
                                     {"actor_id": labels[pick][0], "name": labels[pick][1]})
    else:
        camps = require("/campaigns", {"limit": 200})
        if camps:
            labels = {f"{c['campaign_name']} (#{c['id']})": (c["id"], c["campaign_name"]) for c in camps}
            pick = st.selectbox("Campaign", list(labels))
            if st.button("Investigate"):
                resp, err = api_post("/ai/investigate/campaign",
                                     {"campaign_id": labels[pick][0], "name": labels[pick][1]})
    if err:
        st.error(err)
    elif resp:
        render_ai_response(resp)


def attack_path_investigator():
    ui.page_header("Attack Path Investigator")
    alerts = require("/wazuh/enriched-alerts", {"limit": 50})
    if not alerts:
        st.info("No enriched alerts.")
        return
    labels = {f"[{(a.get('enrichment') or {}).get('priority_level','?')}] "
              f"{a.get('description','')[:50]} (#{a['id']})": a["id"] for a in alerts}
    pick = st.selectbox("Alert", list(labels))
    if st.button("Investigate attack paths", type="primary"):
        resp, err = api_post("/ai/investigate/path", {"alert_id": labels[pick]})
        if err:
            st.error(err)
        else:
            render_ai_response(resp)
            gdata, gerr = api_get(f"/graph/alert/{labels[pick]}")
            if not gerr and gdata and gdata.get("nodes"):
                render_network(gdata, "Attack-path graph")


def threat_actor_investigator():
    ui.page_header("Threat Actor Investigator")
    actors = require("/actors", {"limit": 200})
    if not actors:
        st.info("No threat actors.")
        return
    labels = {f"{a['actor_name']} (#{a['id']})": (a["id"], a["actor_name"]) for a in actors}
    pick = st.selectbox("Threat actor", list(labels))
    if st.button("Investigate", type="primary"):
        aid, name = labels[pick]
        resp, err = api_post("/ai/investigate/actor", {"actor_id": aid, "name": name})
        if err:
            st.error(err)
        else:
            render_ai_response(resp)
            gdata, gerr = api_get(f"/graph/actor/{aid}")
            if not gerr and gdata and gdata.get("nodes"):
                render_network(gdata, f"{name} ecosystem")


def ai_risk_advisor():
    ui.page_header("AI Risk Advisor")
    st.caption("Ask why a CVE is risky, or review the platform's most dangerous CVEs.")
    cve = st.text_input("Explain risk for CVE", value="")
    if st.button("Explain risk") and cve.strip():
        resp, err = api_post("/ai/investigate/cve", {"cve_id": cve.strip()})
        if err:
            st.error(err)
        else:
            render_ai_response(resp)
    st.divider()
    st.subheader("Most dangerous CVEs (AI summary)")
    resp, err = api_post("/ai/query", {"question": "What are the most dangerous CVEs in my environment?"})
    if not err and resp:
        st.write(resp.get("answer", ""))
        cves = resp.get("findings", {}).get("cves", [])
        if cves:
            st.dataframe(pd.DataFrame(cves), width="stretch", hide_index=True)


# ── Phase 14: Agentic SOC Analyst pages ─────────────────────
def _render_report(rep: dict):
    st.subheader("Executive summary")
    st.info(rep.get("executive_summary", ""))
    ra = rep.get("risk_assessment", {})
    c1, c2, c3 = st.columns(3)
    c1.metric("Risk level", ra.get("level", "n/a"))
    c2.metric("Confidence", rep.get("confidence_score", "n/a"))
    c3.metric("Blast radius", (rep.get("blast_radius", {}) or {}).get("total_affected", 0))
    if ra.get("factors"):
        st.markdown("**Risk factors:** " + "; ".join(ra["factors"]))
    ap = rep.get("attack_path_analysis", {})
    if ap.get("paths"):
        st.markdown(f"**Attack paths ({ap.get('count', 0)}):**")
        for p in ap["paths"][:10]:
            st.write(f"- {p}")
    st.subheader("Recommendations")
    for r in rep.get("recommendations", []):
        st.markdown(f"- **{r['action']}** — {r['detail']}  _(evidence: {r['evidence']})_")
    st.caption(f"Evidence sources: {', '.join(rep.get('evidence_sources', []))}")


def _render_plan(result: dict):
    with st.expander("Investigation plan & tool executions", expanded=False):
        for s in result.get("plan", []):
            st.write(f"{s['step']}. **{s['tool']}** — {s['rationale']}")
        st.markdown("**Tool-call log:**")
        df = pd.DataFrame(result.get("tool_calls", []))
        if not df.empty:
            st.dataframe(df[["step", "tool", "status", "summary"]], width="stretch", hide_index=True)


def agentic_soc_analyst():
    ui.page_header("Agentic SOC Analyst")
    st.caption("Autonomous, evidence-driven investigations that plan, correlate, "
               "prioritize, explain, and recommend.")
    kind = st.selectbox("Investigate", ["alert", "cve", "actor", "campaign"])
    result = None
    if kind == "alert":
        alerts = require("/wazuh/enriched-alerts", {"limit": 50})
        if alerts:
            labels = {f"[{(a.get('enrichment') or {}).get('priority_level','?')}] "
                      f"{a.get('description','')[:50]} (#{a['id']})": a["id"] for a in alerts}
            pick = st.selectbox("Alert", list(labels))
            if st.button("Run investigation"):
                result, err = api_post("/agent/investigate/alert", {"alert_id": labels[pick]})
                if err:
                    st.error(err); return
    elif kind == "cve":
        cve = st.text_input("CVE ID", value="")
        if cve and st.button("Run investigation"):
            result, err = api_post("/agent/investigate/cve", {"cve_id": cve.strip()})
            if err:
                st.error(err); return
    elif kind == "actor":
        actors = require("/actors", {"limit": 200})
        if actors:
            names = {f"{a['actor_name']} (#{a['id']})": (a["id"], a["actor_name"]) for a in actors}
            pick = st.selectbox("Actor", list(names))
            if st.button("Run investigation"):
                result, err = api_post("/agent/investigate/actor",
                                       {"actor_id": names[pick][0], "name": names[pick][1]})
                if err:
                    st.error(err); return
    else:
        camps = require("/campaigns", {"limit": 200})
        if camps:
            names = {f"{c['campaign_name']} (#{c['id']})": (c["id"], c["campaign_name"]) for c in camps}
            pick = st.selectbox("Campaign", list(names))
            if st.button("Run investigation"):
                result, err = api_post("/agent/investigate/campaign",
                                       {"campaign_id": names[pick][0], "name": names[pick][1]})
                if err:
                    st.error(err); return
    if result:
        st.success(f"Investigation #{result['investigation_id']} complete.")
        _render_report(result["report"])
        _render_plan(result)


def autonomous_investigations():
    ui.page_header("Autonomous Investigations")
    hist = require("/agent/history", {"limit": 100})
    if not hist:
        st.info("No investigations yet. Run one from the Agentic SOC Analyst page.")
        return
    st.dataframe(pd.DataFrame(hist)[["id", "investigation_type", "target", "risk_level",
                 "confidence", "created_at"]], width="stretch", hide_index=True)
    inv_id = st.number_input("Open investigation #", min_value=1,
                             value=int(hist[0]["id"]), step=1)
    if st.button("Open"):
        data, err = api_post("/agent/report", {"investigation_id": int(inv_id)})
        if err or not data:
            st.error(err or "not found"); return
        st.caption(f"Lineage: {data.get('lineage')}")
        _render_report(data["report"])


def blast_radius_explorer():
    ui.page_header("Blast Radius Explorer")
    c1, c2 = st.columns(2)
    etype = c1.selectbox("Entity type", ["alert", "cve", "actor", "campaign", "community"])
    eid = c2.text_input("Entity ID")
    if eid and st.button("Compute blast radius"):
        data, err = api_post("/agent/blast-radius", {"entity_type": etype, "entity_id": eid.strip()})
        if err or not data:
            st.error(err or "no data"); return
        st.metric("Total affected entities", data.get("total_affected", 0))
        counts = data.get("counts", {})
        df = pd.DataFrame(sorted(counts.items(), key=lambda kv: kv[1], reverse=True),
                          columns=["category", "count"])
        st.plotly_chart(px.bar(df, x="count", y="category", orientation="h",
                               title="Blast radius by category").update_layout(
                               height=360, yaxis={"categoryorder": "total ascending"}), width="stretch")
        for cat, items in data.get("affected", {}).items():
            if items:
                with st.expander(f"{cat} ({len(items)})"):
                    st.write(", ".join(str(x) for x in items[:80]))


def risk_explanation_center():
    ui.page_header("Risk Explanation Center")
    st.caption("Why is this alert/CVE critical? Evidence-based explanation.")
    kind = st.radio("Explain", ["alert", "cve"], horizontal=True)
    result = None
    if kind == "alert":
        alerts = require("/wazuh/enriched-alerts", {"limit": 50})
        labels = {f"#{a['id']} [{(a.get('enrichment') or {}).get('priority_level','?')}] "
                  f"{a.get('description','')[:45]}": a["id"] for a in alerts}
        if labels:
            pick = st.selectbox("Alert", list(labels))
            if st.button("Explain risk"):
                result, err = api_post("/agent/investigate/alert", {"alert_id": labels[pick]})
                if err:
                    st.error(err); return
    else:
        cve = st.text_input("CVE ID")
        if cve and st.button("Explain risk"):
            result, err = api_post("/agent/investigate/cve", {"cve_id": cve.strip()})
            if err:
                st.error(err); return
    if result:
        ra = result["report"]["risk_assessment"]
        st.metric("Risk level", ra.get("level", "n/a"))
        st.info(ra.get("explanation", ""))
        for f in ra.get("factors", []):
            st.write(f"- {f}")


def investigation_reports():
    ui.page_header("Investigation Reports")
    hist = require("/agent/history", {"limit": 100})
    if not hist:
        st.info("No reports yet.")
        return
    labels = {f"#{h['id']} {h['investigation_type']} {h['target']} ({h['risk_level']})": h["id"]
              for h in hist}
    pick = st.selectbox("Report", list(labels))
    data, err = api_post("/agent/report", {"investigation_id": labels[pick]})
    if err or not data:
        st.error(err or "not found"); return
    rep = data["report"]
    _render_report(rep)
    with st.expander("Full structured report (JSON)"):
        st.json(rep)


# ── Phase 15: reporting pages ───────────────────────────────
def _latest_report(report_type):
    lst = require("/reports", {"report_type": report_type, "limit": 1})
    if not lst:
        return None
    data, err = api_get(f"/reports/{lst[0]['id']}")
    return None if err else data


def soc_briefings():
    ui.page_header("SOC Briefings (Daily)")
    if st.button("Generate today's briefing"):
        api_post("/reports/daily", {})
        st.cache_data.clear()
    rep = _latest_report("daily_briefing")
    if not rep:
        st.info("No daily briefing yet — click generate."); return
    r = rep["report_json"]
    st.caption(f"Generated {rep['generated_at']}")
    cas = r.get("critical_alerts_summary", {})
    st.subheader("Critical alerts")
    st.plotly_chart(level_bar(cas.get("by_level", {}), "Alerts by SOC priority"), width="stretch")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Top threat actors**"); st.dataframe(pd.DataFrame(r.get("top_threat_actors", [])),
                                                           width="stretch", hide_index=True)
        st.markdown("**Emerging risks**"); st.dataframe(pd.DataFrame(r.get("emerging_risks", [])),
                                                        width="stretch", hide_index=True)
    with c2:
        st.markdown("**New attack paths**")
        for p in r.get("new_attack_paths", [])[:8]:
            st.write(f"- {p}")
        st.markdown("**Detection gaps**"); st.dataframe(pd.DataFrame(r.get("detection_gaps", [])),
                                                        width="stretch", hide_index=True)


def cti_reports():
    ui.page_header("CTI Reports (Weekly)")
    if st.button("Generate weekly CTI report"):
        api_post("/reports/weekly", {})
        st.cache_data.clear()
    rep = _latest_report("weekly_cti")
    if not rep:
        st.info("No weekly report yet — click generate."); return
    r = rep["report_json"]
    st.caption(f"Generated {rep['generated_at']}")
    c1, c2, c3 = st.columns(3)
    land = r.get("threat_landscape", {})
    c1.metric("CVEs", land.get("cves", 0)); c2.metric("Actors", land.get("threat_actors", 0))
    c3.metric("Predictions", land.get("predictions", 0))
    st.markdown("**Threat actor activity**")
    st.dataframe(pd.DataFrame(r.get("threat_actor_activity", [])), width="stretch", hide_index=True)
    c1, c2 = st.columns(2)
    c1.json(r.get("cve_trends", {})); c2.json(r.get("risk_trends", {}))


def investigation_history():
    ui.page_header("Investigation History")
    hist = require("/agent/history", {"limit": 100})
    if hist:
        st.dataframe(pd.DataFrame(hist)[["id", "investigation_type", "target", "risk_level",
                     "confidence", "created_at"]], width="stretch", hide_index=True)
    else:
        st.info("No investigations recorded yet.")


def autonomous_triage_center():
    ui.page_header("Autonomous Triage Center")
    st.caption("Detect critical findings and auto-run agent investigations.")
    max_alerts = st.slider("Max alerts to auto-investigate", 1, 25, 10)
    if st.button("Run autonomous triage"):
        data, err = api_post("/reports/generate", {"report_type": "triage", "max_alerts": max_alerts})
        if err:
            st.error(err)
        else:
            st.success(f"Investigated {data['investigated']} critical alert(s).")
            st.json(data.get("candidates", {}))
        st.cache_data.clear()
    rep = _latest_report("autonomous_triage")
    if rep:
        st.subheader("Latest triage run")
        st.caption(rep["report_json"].get("summary", ""))
        st.dataframe(pd.DataFrame(rep["report_json"].get("investigations", [])),
                     width="stretch", hide_index=True)


# ── Phase 16: predictive intelligence pages ─────────────────
def predictive_intelligence_center():
    ui.page_header("Predictive Intelligence Center")
    preds = require("/predictions", {"limit": 500})
    if not preds:
        st.info("No predictions yet. Run `python -m backend.app.predictions.link_prediction`."); return
    df = pd.DataFrame(preds)
    df["pair"] = df["source_type"] + "→" + df["target_type"]
    counts = df["pair"].value_counts().reset_index()
    counts.columns = ["pair", "count"]
    c1, c2 = st.columns(2)
    c1.metric("Predicted relationships", len(df))
    c2.metric("Avg confidence", round(df["confidence"].mean(), 3))
    st.plotly_chart(px.bar(counts, x="count", y="pair", orientation="h",
                           title="Predicted relationships by type").update_layout(height=320,
                           yaxis={"categoryorder": "total ascending"}), width="stretch")
    st.dataframe(df[["source_type", "source_id", "target_type", "target_id", "confidence", "model"]],
                 width="stretch", hide_index=True)


def predicted_threat_actors():
    ui.page_header("Predicted Threat Actors")
    st.caption("Emerging actor relationships predicted from graph embeddings.")
    rows = require("/predictions/actors", {"limit": 200})
    ins = require("/graph/insights", {"insight_type": "prediction_emerging_actor", "limit": 50})
    if ins:
        st.subheader("Emerging actor insights")
        for i in ins:
            st.write(f"- {i['insight']}")
    st.dataframe(pd.DataFrame(rows) if rows else pd.DataFrame(),
                 width="stretch", hide_index=True)


def predicted_cves():
    ui.page_header("Predicted High-Risk CVEs")
    rows = require("/predictions/cves", {"limit": 200})
    ins = require("/graph/insights", {"insight_type": "prediction_high_risk_cve", "limit": 50})
    if ins:
        for i in ins[:15]:
            st.write(f"- {i['insight']}")
    if rows:
        st.dataframe(pd.DataFrame(rows)[["source_type", "source_id", "target_id", "confidence"]],
                     width="stretch", hide_index=True)


def emerging_campaigns():
    ui.page_header("Emerging Campaigns")
    rows = require("/predictions/campaigns", {"limit": 200})
    ins = require("/graph/insights", {"insight_type": "prediction_emerging_campaign", "limit": 50})
    if ins:
        for i in ins:
            st.write(f"- {i['insight']}")
    st.dataframe(pd.DataFrame(rows) if rows else pd.DataFrame(), width="stretch", hide_index=True)


def graph_embedding_explorer():
    ui.page_header("Graph Embedding Explorer")
    st.caption("FastRP embeddings (stored in Neo4j) drive link prediction. Below: the "
               "predicted-relationship network derived from embedding similarity.")
    preds = require("/predictions", {"limit": 150})
    if not preds:
        st.info("No predictions to visualize."); return
    nodes, ids = [], set()
    edges = []
    for p in preds:
        for t, i in [(p["source_type"], p["source_id"]), (p["target_type"], p["target_id"])]:
            nid = f"{t.capitalize()}:{i}"
            if nid not in ids:
                ids.add(nid)
                nodes.append({"id": nid, "label": t.capitalize(), "name": i})
        edges.append({"source": f"{p['source_type'].capitalize()}:{p['source_id']}",
                      "target": f"{p['target_type'].capitalize()}:{p['target_id']}", "type": "PREDICTED"})
    render_network({"nodes": nodes, "edges": edges}, "Predicted relationship network")


# ── Phase 17: detection coverage pages ──────────────────────
def attack_coverage_center():
    ui.page_header("ATT&CK Coverage Center")
    cov = require("/coverage")
    c1, c2, c3 = st.columns(3)
    c1.metric("Coverage", f"{cov['coverage_pct']}%")
    c2.metric("Observed techniques", cov["observed"])
    c3.metric("Unobserved", cov["unobserved"])
    bt = cov.get("by_tactic", {})
    df = pd.DataFrame([{"tactic": k, "coverage_pct": v["pct"], "observed": v["observed"],
                        "total": v["total"]} for k, v in bt.items()]).sort_values("coverage_pct")
    st.plotly_chart(px.bar(df, x="coverage_pct", y="tactic", orientation="h",
                           title="Coverage % by tactic").update_layout(height=420), width="stretch")


def detection_gap_explorer():
    ui.page_header("Detection Gap Explorer")
    gaps = require("/coverage/gaps")
    for name, g in gaps.items():
        st.subheader(f"{name.replace('_', ' ').title()} ({g['count']})")
        if g["items"]:
            st.dataframe(pd.DataFrame(g["items"]), width="stretch", hide_index=True)


def coverage_heatmaps():
    ui.page_header("Coverage Heatmaps")
    cov = require("/coverage")
    bt = cov.get("by_tactic", {})
    df = pd.DataFrame([{"tactic": k, "pct": v["pct"]} for k, v in bt.items()])
    if not df.empty:
        fig = px.imshow([df["pct"].tolist()], x=df["tactic"].tolist(), y=["coverage %"],
                        color_continuous_scale="RdYlGn", text_auto=True, aspect="auto",
                        title="Tactic coverage heatmap")
        fig.update_layout(height=240)
        st.plotly_chart(fig, width="stretch")
    bs = cov.get("by_severity", {})
    st.markdown("**Coverage by risk band**")
    st.dataframe(pd.DataFrame([{"band": k, **v} for k, v in bs.items()]), width="stretch", hide_index=True)


def coverage_trends():
    ui.page_header("Coverage Trends")
    cov = require("/coverage")
    st.metric("Overall coverage", f"{cov['coverage_pct']}%")
    bs = cov.get("by_severity", {})
    df = pd.DataFrame([{"risk_band": k, "coverage_pct": v["pct"], "total": v["total"]}
                       for k, v in bs.items()])
    if not df.empty:
        st.plotly_chart(px.bar(df, x="risk_band", y="coverage_pct",
                               title="Coverage % by technique risk band", text="coverage_pct")
                        .update_layout(height=360), width="stretch")
    st.caption("Re-run coverage over time to build a historical trend.")


def detection_engineering_advisor():
    ui.page_header("Detection Engineering Advisor")
    recs = require("/coverage/recommendations")
    items = recs.get("recommendations", [])
    if not items:
        st.success("No high-risk detection gaps outstanding."); return
    st.caption(f"{len(items)} prioritized detection-engineering recommendations.")
    for r in items:
        st.markdown(f"- **[{r['severity']}]** {r['recommendation']}")


# ── Phase 18: orchestration pages ───────────────────────────
def pipeline_operations_center():
    ui.page_header("Pipeline Operations Center")
    h = require("/pipeline/health")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total runs", h["total_runs"])
    c2.metric("Success rate", f"{h['success_rate']}%")
    c3.metric("Failure rate", f"{h['failure_rate']}%")
    c4.metric("Avg runtime", f"{h.get('avg_runtime_seconds') or 0}s")
    st.caption(f"Scheduler running: {h['scheduler_running']}")
    st.subheader("Run the autonomous pipeline")
    st.caption("Runs the internal dependency-ordered pipeline (collectors excluded by default).")
    if st.button("▶ Run full pipeline"):
        with st.spinner("Running pipeline (this can take ~1-2 minutes)..."):
            res, err = api_post("/pipeline/run", {}, timeout=600)
        if err:
            st.error(err)
        else:
            st.success(f"{res['succeeded']}/{res['total']} steps succeeded.")
            st.dataframe(pd.DataFrame(res["steps"]), width="stretch", hide_index=True)
        st.cache_data.clear()


def scheduler_dashboard():
    ui.page_header("Scheduler Dashboard")
    data = require("/pipeline/jobs")
    st.caption(f"Scheduler running: {data['scheduler_running']} "
               "(set ORCHESTRATION_ENABLED=true to activate cron execution).")
    st.dataframe(pd.DataFrame(data["jobs"]), width="stretch", hide_index=True)


def pipeline_history():
    ui.page_header("Pipeline History")
    job = st.text_input("Filter by job name (optional)")
    params = {"limit": 100}
    if job:
        params["job_name"] = job
    rows = require("/pipeline/history", params)
    if rows:
        df = pd.DataFrame(rows)[["id", "job_name", "job_type", "status", "records_processed",
                                 "duration_seconds", "started_at", "error_message"]]
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("No pipeline runs yet — run the pipeline from the Operations Center.")


def job_monitoring():
    ui.page_header("Job Monitoring")
    h = require("/pipeline/health")
    per_job = h.get("per_job", {})
    if per_job:
        rows = [{"job": k, **v} for k, v in per_job.items()]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.subheader("Run / retry a single job")
    jobs = [j["job"] for j in require("/pipeline/jobs")["jobs"]]
    job = st.selectbox("Job", jobs)
    c1, c2 = st.columns(2)
    if c1.button("Run job"):
        r, err = api_post(f"/pipeline/run/{job}", {}, timeout=600)
        st.error(err) if err else st.success(f"{job}: {r['status']} ({r['records_processed']} records)")
        st.cache_data.clear()
    if c2.button("Retry job"):
        r, err = api_post(f"/pipeline/retry/{job}", {}, timeout=600)
        st.error(err) if err else st.success(f"{job}: {r['status']}")
        st.cache_data.clear()


def autonomous_operations_center():
    ui.page_header("Autonomous Operations Center")
    st.caption("Investigation rules: auto-investigate Wazuh level ≥10, KEV, EPSS≥0.80, "
               "predicted conf>0.80; queue level 7-9 / EPSS 0.50-0.79; ignore the rest.")
    if st.button("Run autonomous triage now"):
        r, err = api_post("/pipeline/run/autonomous_triage", {}, timeout=600)
        if err:
            st.error(err)
        else:
            st.success(f"Triage: {r['status']} — {r['records_processed']} investigated.")
            st.json(r.get("metadata", {}))
        st.cache_data.clear()
    q = _latest_report("investigation_queue")
    if q:
        rj = q["report_json"]
        st.subheader("Investigation queue")
        st.caption(rj.get("summary", ""))
        st.dataframe(pd.DataFrame(rj.get("queued_alerts", [])), width="stretch", hide_index=True)
    st.subheader("Recent agent investigations")
    hist = require("/agent/history", {"limit": 20})
    if hist:
        st.dataframe(pd.DataFrame(hist)[["id", "investigation_type", "target", "risk_level",
                     "confidence"]], width="stretch", hide_index=True)


def soar_integration_center():
    ui.page_header("SOAR Integration Center")
    st.caption("Ticketing/SOAR abstraction — Mock (default), Jira, TheHive, Shuffle (webhook). "
               "Configured via TICKET_PROVIDER + provider env vars; investigations/reports export "
               "automatically during autonomous triage.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Providers", 4)
    c2.metric("Default", "mock")
    c3.metric("Shuffle", "webhook-ready")
    c4.metric("Creds required", "no")
    st.subheader("Latest investigation-queue export")
    q = _latest_report("investigation_queue")
    if q:
        st.json({"summary": q["report_json"].get("summary"),
                 "epss_auto_candidates": q["report_json"].get("epss_auto_candidates"),
                 "predicted_auto_candidates": q["report_json"].get("predicted_auto_candidates")})
    st.subheader("Pipeline jobs feeding SOAR")
    jobs = [j for j in require("/pipeline/jobs")["jobs"]
            if j["job_type"] in ("soc", "reporting")]
    st.dataframe(pd.DataFrame(jobs), width="stretch", hide_index=True)


# ── Phase 19: human-in-the-loop response pages ──────────────
def response_recommendations():
    ui.page_header("Response Recommendations")
    st.caption("Evidence-based response actions derived from agent investigations. "
               "Nothing executes without analyst approval.")
    s = require("/response/stats")
    cols = st.columns(len(s.get("by_status", {})) or 1)
    for c, (status, n) in zip(cols, s.get("by_status", {}).items()):
        c.metric(status.capitalize(), n)
    c1, c2 = st.columns([1, 2])
    if c1.button("Generate from recent investigations"):
        r, err = api_post("/response/generate", {"limit": 10})
        st.error(err) if err else st.success(f"Created {r.get('recommendations_created', 0)} recommendation(s).")
        st.cache_data.clear()
    status = c2.selectbox("Filter status", ["all", "pending", "approved", "executed", "verified", "rejected", "failed"])
    params = {"limit": 200}
    if status != "all":
        params["status"] = status
    rows = require("/response/recommendations", params)
    if rows:
        st.dataframe(pd.DataFrame(rows)[["id", "action_type", "title", "severity", "status",
                     "approved_by", "verified"]], width="stretch", hide_index=True)
    else:
        st.info("No recommendations — generate some above.")


def approval_queue():
    ui.page_header("Approval Queue")
    st.caption("Review pending recommendations. Approval is required before any execution.")
    approver = st.text_input("Analyst name (approver)", value="analyst")
    pending = require("/response/recommendations", {"status": "pending", "limit": 100})
    if not pending:
        st.success("No pending recommendations awaiting approval."); return
    for r in pending:
        with st.expander(f"#{r['id']} [{r['severity']}] {r['title']} ({r['action_type']})"):
            st.write(r.get("description", ""))
            st.caption(r.get("rationale", ""))
            c1, c2 = st.columns(2)
            if c1.button("✅ Approve", key=f"appr{r['id']}"):
                _, err = api_post(f"/response/recommendations/{r['id']}/approve", {"approver": approver})
                st.error(err) if err else st.success("Approved."); st.cache_data.clear()
            if c2.button("❌ Reject", key=f"rej{r['id']}"):
                _, err = api_post(f"/response/recommendations/{r['id']}/reject",
                                  {"approver": approver, "reason": "rejected via dashboard"})
                st.error(err) if err else st.warning("Rejected."); st.cache_data.clear()


def action_execution_center():
    ui.page_header("Action Execution Center")
    st.caption("Execute APPROVED actions through Shuffle (SOAR), then verify. "
               "Only approved recommendations can be executed.")
    actor = st.text_input("Operator", value="analyst")
    approved = require("/response/recommendations", {"status": "approved", "limit": 100})
    executed = require("/response/recommendations", {"status": "executed", "limit": 100})

    st.subheader(f"Approved — ready to execute ({len(approved)})")
    for r in approved:
        c1, c2 = st.columns([3, 1])
        c1.write(f"#{r['id']} [{r['severity']}] {r['title']} — approved by {r['approved_by']}")
        if c2.button("▶ Execute", key=f"exec{r['id']}"):
            res, err = api_post(f"/response/recommendations/{r['id']}/execute", {"actor": actor})
            st.error(err) if err else st.success(f"Executed via {res['execution_result'].get('provider')}.")
            st.cache_data.clear()

    st.subheader(f"Executed — verify ({len(executed)})")
    for r in executed:
        c1, c2 = st.columns([3, 1])
        c1.write(f"#{r['id']} {r['title']} — ref {(r.get('execution_result') or {}).get('ticket_id')}")
        if c2.button("🔎 Verify", key=f"ver{r['id']}"):
            res, err = api_post(f"/response/recommendations/{r['id']}/verify", {"actor": actor})
            st.error(err) if err else st.success(f"Verified: {res['verified']}")
            st.cache_data.clear()


def response_audit_trail():
    ui.page_header("Response Audit Trail")
    st.caption("Append-only log of every response action transition (who, what, when).")
    rows = require("/response/audit", {"limit": 300})
    if rows:
        df = pd.DataFrame(rows)[["id", "recommendation_id", "event", "actor", "created_at"]]
        st.dataframe(df, width="stretch", hide_index=True)
        counts = df["event"].value_counts().reset_index()
        counts.columns = ["event", "count"]
        st.plotly_chart(px.bar(counts, x="count", y="event", orientation="h",
                               title="Audit events").update_layout(height=300,
                               yaxis={"categoryorder": "total ascending"}), width="stretch")
    else:
        st.info("No audit events yet.")


def soar_response_center():
    ui.page_header("SOAR Response Center")
    st.caption("End-to-end response flow: agent evidence → recommendation → approval → "
               "Shuffle execution → verification → audit. No autonomous execution.")
    s = require("/response/stats")
    by = s.get("by_status", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", s.get("total", 0))
    c2.metric("Pending approval", by.get("pending", 0))
    c3.metric("Executed", by.get("executed", 0) + by.get("verified", 0))
    c4.metric("Verified", by.get("verified", 0))
    if by:
        df = pd.DataFrame(sorted(by.items(), key=lambda kv: kv[1], reverse=True), columns=["status", "count"])
        st.plotly_chart(px.bar(df, x="status", y="count", title="Recommendations by status", text="count")
                        .update_layout(height=340), width="stretch")
    st.markdown("**SOAR provider:** reuses the existing ticketing framework "
                "(`TICKET_PROVIDER` — Mock default, Shuffle webhook when configured). "
                "Approved actions are executed via `ShuffleProvider`; execution + verification are audited.")
    st.subheader("Recently verified actions")
    verified = require("/response/recommendations", {"status": "verified", "limit": 20})
    if verified:
        st.dataframe(pd.DataFrame(verified)[["id", "action_type", "title", "approved_by", "executed_at"]],
                     width="stretch", hide_index=True)


PAGE_FUNCS = {
    "Executive Overview": executive_overview,
    "Threat Intelligence Overview": ti_overview,
    "Risk Analysis": risk_analysis,
    "ATT&CK Analysis": attack_analysis,
    "CVE Analysis": cve_analysis,
    "Correlation Explorer": correlation_explorer,
    "EPSS Analysis": epss_analysis,
    "KEV Analysis": kev_analysis,
    "Threat Prioritization": threat_prioritization,
    "SOC Readiness": soc_readiness,
    "MISP Intelligence Overview": misp_overview,
    "Threat Actors": threat_actors_page,
    "Malware Analysis": malware_page,
    "IOC Explorer": ioc_explorer,
    "Campaign Explorer": campaign_explorer,
    "Threat Intelligence Relationships": ti_relationships,
    "SOC Overview": soc_overview,
    "Live Alerts": live_alerts,
    "Threat-Enriched Alerts": threat_enriched_alerts,
    "Threat Actor Activity": threat_actor_activity,
    "Malware Activity": malware_activity,
    "Campaign Activity": campaign_activity,
    "Priority Queue": priority_queue,
    "Knowledge Graph Overview": knowledge_graph_overview,
    "Threat Actor Graph": threat_actor_graph,
    "Campaign Graph": campaign_graph,
    "Alert Investigation Graph": alert_investigation_graph,
    "CVE Relationship Graph": cve_relationship_graph,
    "Graph Intelligence Center": graph_intelligence_center,
    "Attack Path Explorer": attack_path_explorer,
    "Threat Actor Influence": threat_actor_influence,
    "Campaign Communities": campaign_communities,
    "High-Risk CVEs": high_risk_cves,
    "Graph-Based Risk Analysis": graph_based_risk_analysis,
    "AI Threat Analyst": ai_threat_analyst,
    "Investigation Assistant": investigation_assistant,
    "Attack Path Investigator": attack_path_investigator,
    "Threat Actor Investigator": threat_actor_investigator,
    "AI Risk Advisor": ai_risk_advisor,
    "Agentic SOC Analyst": agentic_soc_analyst,
    "Autonomous Investigations": autonomous_investigations,
    "Blast Radius Explorer": blast_radius_explorer,
    "Risk Explanation Center": risk_explanation_center,
    "Investigation Reports": investigation_reports,
    "SOC Briefings": soc_briefings,
    "CTI Reports": cti_reports,
    "Investigation History": investigation_history,
    "Autonomous Triage Center": autonomous_triage_center,
    "Predictive Intelligence Center": predictive_intelligence_center,
    "Predicted Threat Actors": predicted_threat_actors,
    "Predicted CVEs": predicted_cves,
    "Emerging Campaigns": emerging_campaigns,
    "Graph Embedding Explorer": graph_embedding_explorer,
    "ATT&CK Coverage Center": attack_coverage_center,
    "Detection Gap Explorer": detection_gap_explorer,
    "Coverage Heatmaps": coverage_heatmaps,
    "Coverage Trends": coverage_trends,
    "Detection Engineering Advisor": detection_engineering_advisor,
    "Pipeline Operations Center": pipeline_operations_center,
    "Scheduler Dashboard": scheduler_dashboard,
    "Pipeline History": pipeline_history,
    "Job Monitoring": job_monitoring,
    "Autonomous Operations Center": autonomous_operations_center,
    "SOAR Integration Center": soar_integration_center,
    "Response Recommendations": response_recommendations,
    "Approval Queue": approval_queue,
    "Action Execution Center": action_execution_center,
    "Response Audit Trail": response_audit_trail,
    "SOAR Response Center": soar_response_center,
}
PAGE_FUNCS[page]()
