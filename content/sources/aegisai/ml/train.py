"""Train the threat risk-scoring model (reproducible, versioned).

    python -m ml.train               # train V2 (EPSS + KEV enriched) - the default
    python -m ml.train --version v1  # reproduce the original V1 model

V2 extends V1's features with EPSS score/percentile and CISA KEV presence/age,
and enriches the weak-supervision label with those real-world exploitation
signals. Both versions are archived (risk_model_<version>.joblib) so feature
importance and metrics can be compared; the active model is risk_model.joblib.
"""

import argparse
from datetime import datetime, timezone

import numpy as np
from sklearn.model_selection import train_test_split

from backend.app.database import SessionLocal
from ml.evaluation import level_distribution, regression_metrics, score_distribution
from ml.feature_engineering import (
    FEATURE_COLUMNS,
    FEATURE_COLUMNS_V2,
    FEATURE_COLUMNS_V3,
    FEATURE_COLUMNS_V4,
    FEATURE_COLUMNS_V5,
    FEATURE_COLUMNS_V6,
    build_features,
    build_features_v2,
    build_features_v3,
    build_features_v4,
    build_features_v5,
    build_features_v6,
    compute_weak_labels,
    compute_weak_labels_v2,
    compute_weak_labels_v3,
    compute_weak_labels_v4,
    compute_weak_labels_v5,
    compute_weak_labels_v6,
)
from ml.risk_model import (
    RANDOM_STATE,
    build_model,
    load_archived_metrics,
    model_version,
    save_model,
)


_PREVIOUS = {"v6": "v5", "v5": "v4", "v4": "v3", "v3": "v2", "v2": "v1"}


def _pipeline(version: str):
    if version == "v6":
        return FEATURE_COLUMNS_V6, build_features_v6, compute_weak_labels_v6
    if version == "v5":
        return FEATURE_COLUMNS_V5, build_features_v5, compute_weak_labels_v5
    if version == "v4":
        return FEATURE_COLUMNS_V4, build_features_v4, compute_weak_labels_v4
    if version == "v3":
        return FEATURE_COLUMNS_V3, build_features_v3, compute_weak_labels_v3
    if version == "v2":
        return FEATURE_COLUMNS_V2, build_features_v2, compute_weak_labels_v2
    return FEATURE_COLUMNS, build_features, compute_weak_labels


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the risk-scoring model")
    parser.add_argument("--version", choices=["v1", "v2", "v3", "v4", "v5", "v6"], default="v6")
    args = parser.parse_args()
    version = args.version

    feature_columns, build, label_fn = _pipeline(version)

    print(f"Building {version} features ...")
    with SessionLocal() as db:
        df = build(db)
    if df.empty:
        print("No correlated CVEs found. Run the collectors/correlation engine first.")
        return 1

    y = label_fn(df)
    X = df[feature_columns]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    model, algorithm = build_model()
    print(f"Training {algorithm} ({version}) on {len(X_train)} samples, "
          f"{len(feature_columns)} features ...")
    model.fit(X_train, y_train)

    preds = np.clip(model.predict(X_test), 0, 100)
    metrics = regression_metrics(y_test, preds)
    importances = sorted(
        zip(feature_columns, (float(v) for v in model.feature_importances_)),
        key=lambda kv: kv[1], reverse=True,
    )
    all_preds = np.clip(model.predict(X), 0, 100)

    meta = {
        "algorithm": algorithm,
        "version": version,
        "model_version": model_version(algorithm, version),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_samples": int(len(df)),
        "feature_columns": feature_columns,
        "metrics": metrics,
        "feature_importances": [
            {"feature": f, "importance": round(i, 4)} for f, i in importances
        ],
        "score_distribution": score_distribution(all_preds),
        "level_distribution": level_distribution(all_preds),
    }
    save_model(model, meta, version=version)

    print(f"\nModel: {meta['model_version']}")
    print(f"Held-out metrics: {metrics}")
    print("\nFeature importance ranking:")
    for rank, (feature, imp) in enumerate(importances, 1):
        print(f"  {rank:2d}. {feature:<22} {imp:.4f}")
    print(f"\nScore distribution: {meta['score_distribution']}")
    print(f"Level distribution: {meta['level_distribution']}")

    # Comparison against the previous version when available.
    prev_version = _PREVIOUS.get(version)
    new_features = {
        "v2": ("epss_score", "epss_percentile", "kev_present", "kev_age_days"),
        "v3": ("misp_actor_linked", "misp_actor_count", "misp_max_actor_conf"),
        "v4": ("wazuh_observed", "wazuh_alert_count", "wazuh_max_level"),
        "v5": ("cve_pagerank", "cve_degree", "ta_pagerank", "community_risk",
               "shortest_path_to_alert"),
        "v6": ("node_embedding_norm", "predicted_link_count", "predicted_actor_exposure",
               "community_influence", "graph_similarity"),
    }.get(version, ())
    if prev_version:
        prev = load_archived_metrics(prev_version)
        if prev:
            print(f"\n-- {prev_version} vs {version} comparison --")
            print(f"  {prev_version} metrics: {prev['metrics']}")
            print(f"  {version} metrics: {metrics}")
            print(f"  New features in {version} (importance):")
            for feat in new_features:
                imp = next((d["importance"] for d in meta["feature_importances"]
                            if d["feature"] == feat), 0.0)
                print(f"    {feat:<20} {version}={imp:.4f}")
            print("  Top feature shift:")
            print(f"    {prev_version} #1: {prev['feature_importances'][0]['feature']} "
                  f"({prev['feature_importances'][0]['importance']:.4f})")
            print(f"    {version} #1: {meta['feature_importances'][0]['feature']} "
                  f"({meta['feature_importances'][0]['importance']:.4f})")

    print("\nModel saved. Run `python -m ml.inference` to score CVEs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
