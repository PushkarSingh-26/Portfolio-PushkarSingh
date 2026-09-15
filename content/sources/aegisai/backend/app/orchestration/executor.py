"""Job executor (Phase 18.1 / 18.4).

Runs a registered job with retry + backoff, recording every attempt's outcome to
pipeline_runs for observability and audit. Underlying jobs are idempotent
(upserts / dedup), so retries and restarts never duplicate data.
"""

import logging
import time
import traceback
from datetime import datetime, timezone

from backend.app.config import get_settings
from backend.app.orchestration.jobs import get_job

log = logging.getLogger("orchestration.executor")


def _serialize(run) -> dict:
    return {"id": run.id, "job_name": run.job_name, "job_type": run.job_type,
            "status": run.status, "started_at": run.started_at,
            "completed_at": run.completed_at, "duration_seconds": run.duration_seconds,
            "records_processed": run.records_processed, "error_message": run.error_message,
            "metadata": run.run_metadata}


def run_job(job_name: str, max_retries: int | None = None) -> dict:
    """Execute a job with retry/backoff; persist a pipeline_runs record."""
    from backend.app.database import SessionLocal
    from backend.app.models import PipelineRun

    fn, job_type, _desc, _cron = get_job(job_name)
    settings = get_settings()
    retries = settings.job_max_retries if max_retries is None else max_retries
    backoff = settings.job_retry_backoff_seconds

    started = datetime.now(timezone.utc).replace(tzinfo=None)
    with SessionLocal() as db:
        run = PipelineRun(job_name=job_name, job_type=job_type, status="running", started_at=started)
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id = run.id

    t0 = time.perf_counter()
    result, error = None, None
    for attempt in range(retries + 1):
        try:
            result = fn()
            error = None
            break
        except Exception as exc:  # noqa: BLE001
            error = f"{type(exc).__name__}: {exc}"
            log.warning("job %s attempt %d/%d failed: %s", job_name, attempt + 1, retries + 1, exc)
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
    duration = round(time.perf_counter() - t0, 3)

    with SessionLocal() as db:
        run = db.get(PipelineRun, run_id)
        run.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        run.duration_seconds = duration
        if error is None:
            run.status = "completed"
            run.records_processed = int((result or {}).get("records_processed", 0))
            run.run_metadata = (result or {}).get("metadata", {})
        else:
            run.status = "failed"
            run.error_message = error[:1000]
            run.run_metadata = {"traceback": traceback.format_exc()[-1500:]}
        db.commit()
        db.refresh(run)
        return _serialize(run)
