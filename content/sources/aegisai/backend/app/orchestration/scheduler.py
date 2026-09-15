"""APScheduler integration (Phase 18.2).

Registers all jobs on their production cron schedules. Opt-in: the scheduler is
only started when ORCHESTRATION_ENABLED is true, so tests/dev never auto-run jobs.
Schedules are always introspectable (for monitoring) without starting.
"""

import logging

from backend.app.orchestration.jobs import JOB_REGISTRY

log = logging.getLogger("orchestration.scheduler")

_scheduler = None


def _trigger_str(cron: dict) -> str:
    return ", ".join(f"{k}={v}" for k, v in cron.items())


def scheduled_jobs() -> list[dict]:
    """All jobs + their cron schedule (introspection; no scheduler needed)."""
    jobs = []
    for name, (_fn, job_type, desc, cron) in JOB_REGISTRY.items():
        entry = {"job": name, "job_type": job_type, "description": desc,
                 "schedule": _trigger_str(cron)}
        if _scheduler is not None:
            sj = _scheduler.get_job(name)
            entry["next_run_time"] = str(sj.next_run_time) if sj and sj.next_run_time else None
        jobs.append(entry)
    return jobs


def build_scheduler():
    """Construct (not start) a BackgroundScheduler with all cron jobs."""
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    from backend.app.orchestration import executor

    sched = BackgroundScheduler(timezone="UTC")
    for name, (_fn, _t, _d, cron) in JOB_REGISTRY.items():
        sched.add_job(executor.run_job, CronTrigger(**cron), args=[name], id=name,
                      replace_existing=True, max_instances=1, coalesce=True)
    return sched


def start() -> bool:
    global _scheduler
    if _scheduler and _scheduler.running:
        return True
    _scheduler = build_scheduler()
    _scheduler.start()
    log.info("Orchestration scheduler started with %d jobs", len(JOB_REGISTRY))
    return True


def shutdown() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None


def is_running() -> bool:
    return bool(_scheduler and _scheduler.running)
