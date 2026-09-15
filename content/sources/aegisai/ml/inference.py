"""Score all correlated CVEs with the trained model and upsert risk_scores.

    python -m ml.inference

Idempotent: one risk_scores row per CVE, updated in place on re-run.
"""

from datetime import datetime, timezone

import numpy as np

from backend.app.database import SessionLocal
from ml.evaluation import level_distribution, score_distribution
from ml.feature_engineering import FEATURE_COLUMNS, build_features_v6 as build_superset
from ml.risk_model import load_model, risk_level


def score_all(db) -> dict:
    """Predict risk for every correlated CVE and upsert into risk_scores.

    Version-agnostic: uses whatever feature columns the active model was
    trained on (from its metadata), selected from the V2 feature superset.
    """
    from backend.app.models import RiskScore

    model, meta = load_model()
    version = meta.get("model_version", "unknown")
    feature_columns = meta.get("feature_columns", FEATURE_COLUMNS)

    df = build_superset(db)
    if df.empty:
        return {"scored": 0, "inserted": 0, "updated": 0}

    preds = np.clip(model.predict(df[feature_columns]), 0, 100)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    existing = {r.cve_id: r for r in db.query(RiskScore).all()}
    inserted = updated = 0

    for cve_id, score in zip(df.index, preds):
        score = round(float(score), 2)
        level = risk_level(score)
        current = existing.get(cve_id)
        if current is None:
            db.add(
                RiskScore(
                    cve_id=cve_id,
                    risk_score=score,
                    risk_level=level,
                    model_version=version,
                    generated_at=now,
                )
            )
            inserted += 1
        else:
            current.risk_score = score
            current.risk_level = level
            current.model_version = version
            current.generated_at = now
            updated += 1

    db.commit()
    return {
        "scored": len(df),
        "inserted": inserted,
        "updated": updated,
        "model_version": version,
        "score_distribution": score_distribution(preds),
        "level_distribution": level_distribution(preds),
    }


def main() -> int:
    print("Scoring correlated CVEs ...")
    with SessionLocal() as db:
        stats = score_all(db)
    if stats["scored"] == 0:
        print("No correlated CVEs to score.")
        return 1
    print(
        f"Done. Scored {stats['scored']} CVEs "
        f"(inserted {stats['inserted']}, updated {stats['updated']}) "
        f"with {stats['model_version']}."
    )
    print(f"Score distribution: {stats['score_distribution']}")
    print(f"Level distribution: {stats['level_distribution']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
