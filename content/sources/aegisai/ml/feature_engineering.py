"""Feature engineering for the threat risk-scoring model.

Builds one feature row per *correlated* CVE (a CVE with at least one ATT&CK
correlation) from data already in PostgreSQL, and provides the weak-supervision
label used to train the model (see compute_weak_labels).

Why weak supervision? The platform has no observed ground truth for "risk"
(no exploitation outcomes, no analyst-assigned scores). We therefore derive a
transparent heuristic label from domain knowledge and train a model to learn
it. This bootstraps a smooth, explainable score and — critically — produces a
serving pipeline whose labels can later be replaced by real signals (CISA KEV
"known exploited", FIRST EPSS exploit-probability) without changing the model
or the API. Assumptions and limitations are documented in the README and the
final report.
"""

from collections import defaultdict
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

# The numeric features fed to the model, in a fixed order (reproducibility).
FEATURE_COLUMNS = [
    # CVE features
    "cvss_score",
    "severity_ordinal",
    "published_age_days",
    "description_length",
    # Correlation features
    "max_confidence",
    "avg_confidence",
    "num_mappings",
    "num_high_confidence",
    # ATT&CK features
    "distinct_tactics",
    "technique_popularity",
    # Derived features
    "is_critical",
    "is_high_confidence",
    "correlation_density",
]

# V2 adds real-world exploitation intelligence (EPSS + CISA KEV) on top of V1.
INTEL_COLUMNS = [
    "epss_score",       # FIRST EPSS exploit probability (0-1)
    "epss_percentile",  # EPSS percentile rank (0-1)
    "kev_present",      # 1 if listed in CISA KEV (confirmed exploited)
    "kev_age_days",     # days since KEV listing (0 if not listed)
]
FEATURE_COLUMNS_V2 = FEATURE_COLUMNS + INTEL_COLUMNS

# V3 adds MISP threat-intelligence context (actor attribution) per CVE.
MISP_COLUMNS = [
    "misp_actor_linked",    # 1 if a tracked threat actor exploits this CVE
    "misp_actor_count",     # number of distinct actors linked
    "misp_max_actor_conf",  # strongest actor->cve enrichment confidence
]
FEATURE_COLUMNS_V3 = FEATURE_COLUMNS_V2 + MISP_COLUMNS

# V4 adds live Wazuh SOC telemetry: is this CVE actively matching detections in
# the monitored environment? (CVE <- correlated technique <- Wazuh alert)
WAZUH_COLUMNS = [
    "wazuh_observed",     # 1 if any Wazuh alert technique correlates to this CVE
    "wazuh_alert_count",  # number of such alerts
    "wazuh_max_level",    # max Wazuh rule_level among them (0-15)
]
FEATURE_COLUMNS_V4 = FEATURE_COLUMNS_V3 + WAZUH_COLUMNS

# V5 adds Neo4j graph-topology intelligence (GDS centrality, community, reach).
GRAPH_COLUMNS = [
    "cve_pagerank",            # GDS PageRank of the CVE node
    "cve_degree",              # GDS degree centrality of the CVE
    "ta_pagerank",             # max PageRank of attributed threat actors
    "ta_degree",               # max degree of attributed threat actors
    "technique_degree",        # max degree of correlated techniques
    "community_risk",          # KEV/critical fraction of the CVE's community
    "connected_entities",      # graph neighbours of the CVE
    "related_alerts",          # Wazuh alerts reaching this CVE
    "related_campaigns",       # campaigns reachable via attributed actors
    "related_malware",         # malware families reachable via attributed actors
    "shortest_path_to_alert",  # graph distance to nearest active alert (0 = none)
]
FEATURE_COLUMNS_V5 = FEATURE_COLUMNS_V4 + GRAPH_COLUMNS

# V6 adds predictive-intelligence signals: graph embeddings + link prediction.
PRED_COLUMNS = [
    "node_embedding_norm",       # L2 norm of the CVE's graph embedding (0 if none)
    "predicted_link_count",      # predicted future relationships targeting the CVE
    "predicted_actor_exposure",  # max confidence a tracked actor will target the CVE
    "community_influence",       # relative size of the CVE's graph community
    "graph_similarity",          # GDS node-similarity score of the CVE
]
FEATURE_COLUMNS_V6 = FEATURE_COLUMNS_V5 + PRED_COLUMNS

_SEVERITY_ORDINAL = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
# CVSS proxy used to impute a missing score from qualitative severity.
_SEVERITY_CVSS_PROXY = {1: 2.0, 2: 5.0, 3: 7.5, 4: 9.5}


def _parse_day(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d")
    except ValueError:
        return None


def _reference_now() -> datetime:
    # Naive UTC to match PostgreSQL's timezone-naive timestamps.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def technique_popularity(db: Session) -> dict[str, int]:
    """Global map of technique_id -> number of correlations it participates in."""
    from backend.app.models import CorrelationResult

    rows = db.execute(
        select(CorrelationResult.technique_id, func.count())
        .group_by(CorrelationResult.technique_id)
    ).all()
    return {tid: count for tid, count in rows}


def build_features(db: Session, reference_time: datetime | None = None) -> pd.DataFrame:
    """Return a feature DataFrame indexed by cve_id for all correlated CVEs."""
    from backend.app.models import CVE, CorrelationResult

    reference_time = reference_time or _reference_now()
    popularity = technique_popularity(db)
    max_pop = max(popularity.values()) if popularity else 1

    correlations = db.execute(
        select(
            CorrelationResult.cve_id,
            CorrelationResult.technique_id,
            CorrelationResult.confidence_score,
            CorrelationResult.confidence_level,
            CorrelationResult.tactic,
        )
    ).all()

    by_cve: dict[str, list] = defaultdict(list)
    for row in correlations:
        by_cve[row.cve_id].append(row)

    cve_rows = db.execute(
        select(
            CVE.cve_id,
            CVE.cvss_score,
            CVE.severity,
            CVE.published_date,
            CVE.description,
        )
    ).all()
    cve_map = {row.cve_id: row for row in cve_rows}

    records = []
    for cve_id, items in by_cve.items():
        cve = cve_map.get(cve_id)
        if cve is None:
            continue

        confidences = [i.confidence_score for i in items]
        tactics = {i.tactic for i in items if i.tactic}
        pops = [popularity.get(i.technique_id, 0) for i in items]
        severity = (cve.severity or "").upper()
        sev_ord = _SEVERITY_ORDINAL.get(severity, 0)
        num_mappings = len(items)
        distinct_tactics = len(tactics)
        age = (
            (reference_time - cve.published_date).days
            if cve.published_date is not None
            else None
        )

        records.append(
            {
                "cve_id": cve_id,
                "cvss_score": cve.cvss_score,
                "severity_ordinal": sev_ord,
                "published_age_days": age,
                "description_length": len(cve.description or ""),
                "max_confidence": max(confidences),
                "avg_confidence": sum(confidences) / len(confidences),
                "num_mappings": num_mappings,
                "num_high_confidence": sum(
                    1 for i in items if (i.confidence_level or "") == "HIGH"
                ),
                "distinct_tactics": distinct_tactics,
                "technique_popularity": (sum(pops) / len(pops)) / max_pop,
                "is_critical": 1 if severity == "CRITICAL" else 0,
                "is_high_confidence": 1 if max(confidences) >= 0.7 else 0,
                "correlation_density": (
                    num_mappings / distinct_tactics if distinct_tactics else num_mappings
                ),
            }
        )

    if not records:
        return pd.DataFrame(columns=["cve_id", *FEATURE_COLUMNS]).set_index("cve_id")

    df = pd.DataFrame.from_records(records).set_index("cve_id")

    # ── Imputation ──────────────────────────────────────────
    median_cvss = df["cvss_score"].median()
    if pd.isna(median_cvss):
        median_cvss = 5.0
    df["cvss_score"] = [
        cvss if pd.notna(cvss) else _SEVERITY_CVSS_PROXY.get(sev, median_cvss)
        for cvss, sev in zip(df["cvss_score"], df["severity_ordinal"])
    ]
    median_age = df["published_age_days"].median()
    if pd.isna(median_age):
        median_age = 0
    df["published_age_days"] = df["published_age_days"].fillna(median_age)

    return df[FEATURE_COLUMNS]


def compute_weak_labels(df: pd.DataFrame) -> pd.Series:
    """Heuristic weak-supervision target in [0, 100].

    Weighted blend of severity (CVSS), correlation strength, ATT&CK breadth,
    technique centrality, and recency, with small bumps for critical/high-
    confidence flags. CVSS dominates because it is the most established signal.
    """
    cvss_n = (df["cvss_score"] / 10.0).clip(0, 1)
    conf_n = df["max_confidence"].clip(0, 1)
    map_n = (df["num_mappings"].clip(upper=6) / 6.0)
    pop_n = df["technique_popularity"].clip(0, 1)

    age = df["published_age_days"].clip(lower=0)
    max_age = age.max() if age.max() and age.max() > 0 else 1
    recency_n = 1 - (age / max_age)

    label = 100 * (
        0.50 * cvss_n
        + 0.20 * conf_n
        + 0.15 * map_n
        + 0.10 * pop_n
        + 0.05 * recency_n
    )
    label = label + 3 * df["is_critical"] + 2 * df["is_high_confidence"]
    return label.clip(0, 100)


def build_features_v2(db: Session, reference_time: datetime | None = None) -> pd.DataFrame:
    """V1 features plus EPSS + CISA KEV intelligence columns.

    EPSS/KEV are LEFT-joined: a CVE with no EPSS score gets 0, and one not in
    KEV gets kev_present=0 / kev_age_days=0. This keeps every correlated CVE
    scorable even before the intel feeds have full coverage.
    """
    from backend.app.models import EPSSScore, KEVEntry

    base = build_features(db, reference_time)
    if base.empty:
        return pd.DataFrame(columns=[*FEATURE_COLUMNS_V2]).rename_axis("cve_id")

    reference_time = reference_time or _reference_now()

    epss_map = {
        cve_id: (score, pct)
        for cve_id, score, pct in db.execute(
            select(EPSSScore.cve_id, EPSSScore.epss_score, EPSSScore.percentile)
        ).all()
    }
    kev_map = {
        cve_id: date_added
        for cve_id, date_added in db.execute(
            select(KEVEntry.cve_id, KEVEntry.date_added)
        ).all()
    }

    def _kev_age(cve_id: str) -> float:
        added = _parse_day(kev_map.get(cve_id))
        if added is None:
            return 0.0
        return max(0.0, (reference_time - added).days)

    base["epss_score"] = [epss_map.get(c, (0.0, 0.0))[0] for c in base.index]
    base["epss_percentile"] = [epss_map.get(c, (0.0, 0.0))[1] for c in base.index]
    base["kev_present"] = [1 if c in kev_map else 0 for c in base.index]
    base["kev_age_days"] = [_kev_age(c) for c in base.index]

    return base[FEATURE_COLUMNS_V2]


def build_features_v3(db: Session, reference_time: datetime | None = None) -> pd.DataFrame:
    """V2 features plus MISP threat-intelligence context (actor attribution).

    A CVE that a tracked threat actor is known to exploit (via the enrichment
    graph: actor -> technique -> cve) is materially higher risk than an
    unattributed one, so we surface actor linkage, actor count, and the
    strongest actor->cve confidence as features.
    """
    from collections import defaultdict

    from backend.app.models import CTIRelationship

    base = build_features_v2(db, reference_time)
    if base.empty:
        return pd.DataFrame(columns=[*FEATURE_COLUMNS_V3]).rename_axis("cve_id")

    actor_count: dict[str, int] = defaultdict(int)
    actor_conf: dict[str, float] = defaultdict(float)
    for cve_id, conf in db.execute(
        select(CTIRelationship.target_key, CTIRelationship.confidence).where(
            CTIRelationship.target_type == "cve",
            CTIRelationship.source_type == "actor",
            CTIRelationship.relationship == "exploits_cve",
        )
    ).all():
        actor_count[cve_id] += 1
        actor_conf[cve_id] = max(actor_conf[cve_id], conf)

    base["misp_actor_linked"] = [1 if c in actor_count else 0 for c in base.index]
    base["misp_actor_count"] = [actor_count.get(c, 0) for c in base.index]
    base["misp_max_actor_conf"] = [round(actor_conf.get(c, 0.0), 3) for c in base.index]

    return base[FEATURE_COLUMNS_V3]


def compute_weak_labels_v3(df: pd.DataFrame) -> pd.Series:
    """V2 label plus a threat-attribution bump.

    Known active exploitation by a tracked actor is strong real-world evidence,
    so attributed CVEs get a confidence-weighted boost on top of the V2 score.
    """
    label = compute_weak_labels_v2(df)
    bump = 10.0 * _opt(df, "misp_max_actor_conf").clip(0, 1)
    return (label + bump).clip(0, 100)


def build_features_v4(db: Session, reference_time: datetime | None = None) -> pd.DataFrame:
    """V3 features plus live Wazuh SOC telemetry.

    A CVE whose ATT&CK technique is firing as a Wazuh alert in the monitored
    estate is under *observed* attack - the strongest possible real-world signal.
    We map alerts to CVEs via the existing correlation graph
    (Wazuh alert technique -> correlation_results -> cve).
    """
    from collections import defaultdict

    from backend.app.models import CorrelationResult, WazuhAlert

    base = build_features_v3(db, reference_time)
    if base.empty:
        return pd.DataFrame(columns=[*FEATURE_COLUMNS_V4]).rename_axis("cve_id")

    # technique -> max alert level + alert count observed in Wazuh
    tech_level: dict[str, int] = defaultdict(int)
    tech_alerts: dict[str, int] = defaultdict(int)
    for alert in db.query(WazuhAlert).all():
        for tech in (alert.mitre_techniques or []):
            tech_alerts[tech] += 1
            tech_level[tech] = max(tech_level[tech], alert.rule_level or 0)

    # technique -> cves (from existing correlations)
    tech_to_cves = defaultdict(set)
    for tech, cve in db.execute(
        select(CorrelationResult.technique_id, CorrelationResult.cve_id)
    ).all():
        tech_to_cves[tech].add(cve)

    cve_alert_count: dict[str, int] = defaultdict(int)
    cve_max_level: dict[str, int] = defaultdict(int)
    for tech, count in tech_alerts.items():
        for cve in tech_to_cves.get(tech, set()):
            cve_alert_count[cve] += count
            cve_max_level[cve] = max(cve_max_level[cve], tech_level[tech])

    base["wazuh_observed"] = [1 if c in cve_alert_count else 0 for c in base.index]
    base["wazuh_alert_count"] = [cve_alert_count.get(c, 0) for c in base.index]
    base["wazuh_max_level"] = [cve_max_level.get(c, 0) for c in base.index]

    return base[FEATURE_COLUMNS_V4]


def compute_weak_labels_v4(df: pd.DataFrame) -> pd.Series:
    """V3 label plus an observed-in-environment bump.

    A CVE under active detection in the monitored estate is escalated: the more
    severe the live Wazuh alert, the larger the bump (scaled by rule level).
    """
    label = compute_weak_labels_v3(df)
    observed = _opt(df, "wazuh_observed").clip(0, 1)
    level_n = (_opt(df, "wazuh_max_level") / 15.0).clip(0, 1)
    bump = 12.0 * observed * (0.4 + 0.6 * level_n)
    return (label + bump).clip(0, 100)


def build_features_v5(db: Session, reference_time: datetime | None = None) -> pd.DataFrame:
    """V4 features plus Neo4j graph-topology intelligence.

    Graph features are read from the persisted `graph_metrics` table (populated
    by the GDS analytics job) plus the existing relationship tables, so training
    needs no live Neo4j connection. A CVE that is graph-central, sits in a
    KEV-heavy community, is reachable from an influential actor, or is close to a
    live alert is materially higher real-world risk than a peripheral one.
    """
    from collections import defaultdict

    from backend.app.models import (
        CorrelationResult,
        CTIRelationship,
        GraphMetric,
        KEVEntry,
        ThreatActor,
    )

    base = build_features_v4(db, reference_time)
    if base.empty:
        return pd.DataFrame(columns=[*FEATURE_COLUMNS_V5]).rename_axis("cve_id")

    # CVE graph metrics
    cve_pr, cve_deg, cve_comm = {}, {}, {}
    tech_deg, actor_pr, actor_deg = {}, {}, {}
    for gm in db.query(GraphMetric).all():
        if gm.entity_type == "CVE":
            cve_pr[gm.entity_id] = gm.pagerank
            cve_deg[gm.entity_id] = gm.degree_centrality
            cve_comm[gm.entity_id] = gm.community_id
        elif gm.entity_type == "Technique":
            tech_deg[gm.entity_id] = gm.degree_centrality
        elif gm.entity_type == "ThreatActor":
            actor_pr[gm.entity_id] = gm.pagerank
            actor_deg[gm.entity_id] = gm.degree_centrality

    # Community risk = fraction of KEV/critical CVEs in each community.
    kev_set = {row[0] for row in db.execute(select(KEVEntry.cve_id)).all()}
    comm_total, comm_risky = defaultdict(int), defaultdict(int)
    for cve_id, comm in cve_comm.items():
        if comm is None:
            continue
        comm_total[comm] += 1
        if cve_id in kev_set:
            comm_risky[comm] += 1
    community_risk = {c: (comm_risky[c] / comm_total[c]) for c in comm_total}

    # CVE -> technique (for technique degree)
    cve_techs = defaultdict(list)
    for tech, cve in db.execute(
        select(CorrelationResult.technique_id, CorrelationResult.cve_id)
    ).all():
        cve_techs[cve].append(tech)

    # CVE -> attributed actors (names), actor -> id, actor -> malware/campaign counts
    actor_id_by_name = {a.actor_name: str(a.id) for a in db.query(ThreatActor).all()}
    cve_actors = defaultdict(set)
    actor_malware, actor_campaign = defaultdict(set), defaultdict(set)
    for st, sk, tt, tk in db.execute(
        select(CTIRelationship.source_type, CTIRelationship.source_key,
               CTIRelationship.target_type, CTIRelationship.target_key)
    ).all():
        if {st, tt} == {"actor", "cve"}:
            actor = sk if st == "actor" else tk
            cve = sk if st == "cve" else tk
            cve_actors[cve].add(actor)
        elif st == "actor" and tt == "malware":
            actor_malware[sk].add(tk)
        elif st == "actor" and tt == "campaign":
            actor_campaign[sk].add(tk)

    # Actors that are linked (via an observed CVE) to a live alert.
    observed = set(base.index[base["wazuh_observed"] == 1])
    actors_with_alert = set()
    for cve in observed:
        actors_with_alert.update(cve_actors.get(cve, set()))

    def _row(cve):
        actors = cve_actors.get(cve, set())
        actor_ids = [actor_id_by_name.get(a) for a in actors if a in actor_id_by_name]
        ta_pr = max((actor_pr.get(aid, 0.0) for aid in actor_ids), default=0.0)
        ta_dg = max((actor_deg.get(aid, 0.0) for aid in actor_ids), default=0.0)
        t_deg = max((tech_deg.get(t, 0.0) for t in cve_techs.get(cve, [])), default=0.0)
        rel_malware = len({m for a in actors for m in actor_malware.get(a, set())})
        rel_campaign = len({c for a in actors for c in actor_campaign.get(a, set())})
        comm = cve_comm.get(cve)
        # Distance to nearest active alert: 2 if technique observed, 4 via actor, else 0.
        if cve in observed:
            spath = 2
        elif actors & actors_with_alert:
            spath = 4
        else:
            spath = 0
        return (cve_pr.get(cve, 0.0), cve_deg.get(cve, 0.0), ta_pr, ta_dg, t_deg,
                community_risk.get(comm, 0.0), cve_deg.get(cve, 0.0),
                int(base.loc[cve, "wazuh_alert_count"]), rel_campaign, rel_malware, spath)

    cols = list(zip(*[_row(c) for c in base.index]))
    for name, values in zip(GRAPH_COLUMNS, cols):
        base[name] = values
    return base[FEATURE_COLUMNS_V5]


def compute_weak_labels_v5(df: pd.DataFrame) -> pd.Series:
    """V4 label plus graph-centrality and community-risk escalation.

    Graph-central CVEs (high PageRank), those in KEV-heavy communities, and those
    reachable from influential actors or close to a live alert get a bounded
    boost - encoding that topological importance, not just static severity,
    drives real-world risk.
    """
    label = compute_weak_labels_v4(df)
    pr = _opt(df, "cve_pagerank")
    pr_n = (pr / pr.max()).clip(0, 1) if pr.max() and pr.max() > 0 else pr * 0
    comm_n = _opt(df, "community_risk").clip(0, 1)
    ta = _opt(df, "ta_pagerank")
    ta_n = (ta / ta.max()).clip(0, 1) if ta.max() and ta.max() > 0 else ta * 0
    bump = 8.0 * pr_n + 6.0 * comm_n + 4.0 * ta_n
    return (label + bump).clip(0, 100)


def build_features_v6(db: Session, reference_time: datetime | None = None) -> pd.DataFrame:
    """V5 features plus predictive-intelligence signals (embeddings + link prediction).

    Predicted links and graph similarity are read from PostgreSQL caches; the
    embedding norm is read from Neo4j when available (0 otherwise), so training
    stays robust without a live graph.
    """
    from collections import defaultdict

    from backend.app.models import GraphMetric, PredictedRelationship

    base = build_features_v5(db, reference_time)
    if base.empty:
        return pd.DataFrame(columns=[*FEATURE_COLUMNS_V6]).rename_axis("cve_id")

    sim, comm = {}, {}
    comm_size = defaultdict(int)
    for gm in db.query(GraphMetric).all():
        if gm.entity_type == "CVE":
            sim[gm.entity_id] = gm.node_similarity_score
            comm[gm.entity_id] = gm.community_id
        if gm.community_id is not None:
            comm_size[gm.community_id] += 1
    max_comm = max(comm_size.values()) if comm_size else 1

    pred_count = defaultdict(int)
    pred_actor = defaultdict(float)
    for p in db.query(PredictedRelationship).all():
        if p.target_type == "cve":
            pred_count[p.target_id] += 1
            if p.source_type == "actor":
                pred_actor[p.target_id] = max(pred_actor[p.target_id], p.confidence)

    norms = {}
    try:
        from backend.app.predictions.embeddings import load_embeddings
        import numpy as np
        for (lab, eid), vec in load_embeddings({"CVE"}).items():
            norms[eid] = float(np.linalg.norm(vec))
    except Exception:  # noqa: BLE001 - embeddings optional at train time
        norms = {}

    idx = list(base.index)
    base["node_embedding_norm"] = [round(norms.get(c, 0.0), 4) for c in idx]
    base["predicted_link_count"] = [pred_count.get(c, 0) for c in idx]
    base["predicted_actor_exposure"] = [round(pred_actor.get(c, 0.0), 4) for c in idx]
    base["community_influence"] = [round(comm_size.get(comm.get(c), 0) / max_comm, 4) for c in idx]
    base["graph_similarity"] = [sim.get(c, 0.0) for c in idx]
    return base[FEATURE_COLUMNS_V6]


def compute_weak_labels_v6(df: pd.DataFrame) -> pd.Series:
    """V5 label plus a predicted-exposure escalation.

    A CVE that link prediction expects a tracked actor to target, or that is
    embedded centrally, is elevated - anticipating risk before it materializes.
    """
    label = compute_weak_labels_v5(df)
    exposure = _opt(df, "predicted_actor_exposure").clip(0, 1)
    comm_inf = _opt(df, "community_influence").clip(0, 1)
    bump = 8.0 * exposure + 4.0 * comm_inf
    return (label + bump).clip(0, 100)


def _opt(df: pd.DataFrame, name: str) -> pd.Series:
    """Optional column accessor (0 if absent) for robust label maths."""
    if name in df.columns:
        return df[name]
    return pd.Series(0.0, index=df.index)


def compute_weak_labels_v2(df: pd.DataFrame) -> pd.Series:
    """V2 weak-supervision target enriched with real-world exploitation signal.

    Modeling choice: V1's label was CVSS-dominated and used no exploitation
    evidence. V2 folds in EPSS (a calibrated exploit-probability) and CISA KEV
    (ground truth that a CVE *is* being exploited). KEV-listed CVEs are anchored
    to >= 90 because confirmed in-the-wild exploitation is the strongest signal
    of real risk. The model then learns this target from features that include
    EPSS/KEV, so their importance rises sharply versus V1.
    """
    cvss_n = (df["cvss_score"] / 10.0).clip(0, 1)
    epss_n = _opt(df, "epss_score").clip(0, 1)
    pct_n = _opt(df, "epss_percentile").clip(0, 1)
    conf_n = df["max_confidence"].clip(0, 1)
    map_n = (df["num_mappings"].clip(upper=6) / 6.0)
    pop_n = df["technique_popularity"].clip(0, 1)

    label = 100 * (
        0.30 * cvss_n
        + 0.30 * epss_n
        + 0.10 * pct_n
        + 0.10 * conf_n
        + 0.10 * map_n
        + 0.10 * pop_n
    )
    label = label + 3 * df["is_critical"] + 2 * df["is_high_confidence"]

    # KEV override: confirmed exploited in the wild -> anchor high.
    kev = _opt(df, "kev_present")
    label = label.where(kev == 0, other=label.clip(lower=90))
    return label.clip(0, 100)
