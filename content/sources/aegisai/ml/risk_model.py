"""Model factory, persistence, and risk-level mapping for the scoring engine.

Prefers XGBoost; falls back to scikit-learn's RandomForest if XGBoost is not
available. Both expose ``feature_importances_`` and a uniform fit/predict API,
so the rest of the pipeline is model-agnostic.
"""

import json
from pathlib import Path

import joblib

MODELS_DIR = Path(__file__).resolve().parent / "models"
MODEL_PATH = MODELS_DIR / "risk_model.joblib"
METRICS_PATH = MODELS_DIR / "metrics.json"

RANDOM_STATE = 42

# Risk-level thresholds on the 0-100 score.
RISK_THRESHOLDS = (
    ("CRITICAL", 75.0),
    ("HIGH", 50.0),
    ("MEDIUM", 25.0),
    ("LOW", 0.0),
)


def build_model():
    """Return (estimator, algorithm_name). XGBoost preferred, RF fallback."""
    try:
        from xgboost import XGBRegressor

        model = XGBRegressor(
            n_estimators=400,
            max_depth=5,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=RANDOM_STATE,
            n_jobs=4,
        )
        return model, "xgboost"
    except Exception:
        from sklearn.ensemble import RandomForestRegressor

        model = RandomForestRegressor(
            n_estimators=400,
            max_depth=14,
            random_state=RANDOM_STATE,
            n_jobs=4,
        )
        return model, "random_forest"


def model_version(algorithm: str, version: str = "v1") -> str:
    return f"risk-{algorithm}-{version}"


def archive_paths(version: str) -> tuple[Path, Path]:
    """Per-version artifact paths, kept alongside the active model so V1 and V2
    can be compared after a retrain."""
    return (
        MODELS_DIR / f"risk_model_{version}.joblib",
        MODELS_DIR / f"metrics_{version}.json",
    )


def load_archived_metrics(version: str) -> dict | None:
    _, metrics_path = archive_paths(version)
    if metrics_path.exists():
        return json.loads(metrics_path.read_text(encoding="utf-8"))
    return None


def risk_level(score: float) -> str:
    for level, threshold in RISK_THRESHOLDS:
        if score >= threshold:
            return level
    return "LOW"


def save_model(model, meta: dict, version: str | None = None) -> None:
    """Persist the active model, and (if `version` given) an archived copy so
    multiple model versions coexist for comparison."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    bundle = {"model": model, "meta": meta}
    joblib.dump(bundle, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    if version:
        model_path, metrics_path = archive_paths(version)
        joblib.dump(bundle, model_path)
        metrics_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def load_model():
    """Return (model, meta). Raises FileNotFoundError if not yet trained."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"No trained model at {MODEL_PATH}. Run `python -m ml.train` first."
        )
    bundle = joblib.load(MODEL_PATH)
    return bundle["model"], bundle["meta"]
