"""Explainability for the risk model.

Two complementary views, both dependency-light (no SHAP required):

* Global  - model ``feature_importances_`` plus permutation importance
            (scikit-learn), which is model-agnostic and less biased toward
            high-cardinality features.
* Local   - per-CVE contribution estimate: a feature's standardized deviation
            from the corpus mean, weighted by its global importance. This gives
            an explainable "why is this CVE risky" breakdown without SHAP, and
            can be upgraded to SHAP later without changing callers.
"""

import numpy as np
import pandas as pd

from ml.feature_engineering import FEATURE_COLUMNS


def global_importance(model, feature_columns=FEATURE_COLUMNS) -> list[dict]:
    """Native feature importances, ranked descending."""
    importances = getattr(model, "feature_importances_", None)
    if importances is None:
        return []
    ranked = sorted(
        zip(feature_columns, (float(v) for v in importances)),
        key=lambda kv: kv[1],
        reverse=True,
    )
    return [{"feature": f, "importance": round(i, 4)} for f, i in ranked]


def permutation_importance_ranking(
    model, X: pd.DataFrame, y, feature_columns=FEATURE_COLUMNS
) -> list[dict]:
    """Permutation importance (model-agnostic)."""
    from sklearn.inspection import permutation_importance

    result = permutation_importance(
        model, X[feature_columns], y, n_repeats=5, random_state=42, n_jobs=2
    )
    ranked = sorted(
        zip(feature_columns, (float(v) for v in result.importances_mean)),
        key=lambda kv: kv[1],
        reverse=True,
    )
    return [{"feature": f, "importance": round(i, 4)} for f, i in ranked]


def explain_instance(
    model, x_row: pd.Series, corpus: pd.DataFrame, feature_columns=FEATURE_COLUMNS
) -> list[dict]:
    """Top feature contributions for a single CVE.

    contribution = global_importance * standardized_deviation(feature value).
    Positive => pushes risk up relative to the corpus, negative => pulls it down.
    """
    importances = {d["feature"]: d["importance"] for d in global_importance(model, feature_columns)}
    means = corpus[feature_columns].mean()
    stds = corpus[feature_columns].std().replace(0, 1.0)

    contributions = []
    for feature in feature_columns:
        z = (x_row[feature] - means[feature]) / stds[feature]
        contributions.append(
            {
                "feature": feature,
                "value": round(float(x_row[feature]), 4),
                "contribution": round(float(importances.get(feature, 0.0) * z), 4),
            }
        )
    contributions.sort(key=lambda d: abs(d["contribution"]), reverse=True)
    return contributions


def main() -> int:
    from backend.app.database import SessionLocal
    from ml.feature_engineering import build_features_v6 as build_features_v3
    from ml.risk_model import load_model

    model, meta = load_model()
    feature_columns = meta.get("feature_columns", FEATURE_COLUMNS)
    with SessionLocal() as db:
        df = build_features_v3(db)

    print(f"Model: {meta.get('model_version')}")
    print("\nGlobal feature importance:")
    for rank, item in enumerate(global_importance(model, feature_columns), 1):
        print(f"  {rank:2d}. {item['feature']:<22} {item['importance']:.4f}")

    if not df.empty:
        preds = np.clip(model.predict(df[feature_columns]), 0, 100)
        top_idx = int(np.argmax(preds))
        cve_id = df.index[top_idx]
        print(f"\nExample explanation - highest-risk CVE {cve_id} "
              f"(score {preds[top_idx]:.1f}):")
        for item in explain_instance(model, df.iloc[top_idx], df, feature_columns)[:5]:
            print(f"  {item['feature']:<22} value={item['value']:<10} "
                  f"contribution={item['contribution']:+.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
