"""Cyber Threat Intelligence Platform - FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from backend.app.routers import (
    agent,
    ai,
    correlations,
    coverage,
    cves,
    epss,
    graph,
    health,
    kev,
    misp,
    pipeline,
    predictions,
    priority,
    reports,
    response,
    risk_scores,
    soc,
    techniques,
    wazuh,
)
from backend.app import __version__
from backend.app.config import get_settings
from backend.app.database import engine
from backend.app.models import (  # noqa: F401 - registers models with Base.metadata
    CVE,
    CorrelationResult,
    EPSSScore,
    KEVEntry,
    PriorityScore,
    RiskScore,
    Technique,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is owned by Alembic migrations. Bring the DB up to head on startup
    # (dev convenience; disable with AUTO_MIGRATE=false to manage manually).
    if settings.auto_migrate:
        try:
            from backend.app.db_migrate import run_migrations

            run_migrations()
        except Exception as exc:  # noqa: BLE001 - never block startup on migration
            print(f"[startup] Alembic upgrade skipped/failed: {exc}")

    # Phase 18: start the autonomous orchestration scheduler when enabled.
    if settings.orchestration_enabled:
        try:
            from backend.app.orchestration import scheduler

            scheduler.start()
        except Exception as exc:  # noqa: BLE001
            print(f"[startup] Orchestration scheduler not started: {exc}")

    yield

    try:
        from backend.app.orchestration import scheduler

        scheduler.shutdown()
    except Exception:  # noqa: BLE001
        pass
    # Shutdown: dispose the engine so pooled connections close cleanly.
    engine.dispose()


app = FastAPI(
    title="Cyber Threat Intelligence Platform",
    description="API for collecting, enriching, and serving threat intelligence.",
    version=__version__,
    lifespan=lifespan,
)

app.include_router(health.router, tags=["health"])
app.include_router(techniques.router, tags=["techniques"])
app.include_router(techniques.stats_router)
app.include_router(cves.router)
app.include_router(correlations.router)
app.include_router(risk_scores.router)
app.include_router(epss.router)
app.include_router(kev.router)
app.include_router(priority.router)
app.include_router(soc.router)
app.include_router(misp.router)
app.include_router(wazuh.router)
app.include_router(graph.router)
app.include_router(ai.router)
app.include_router(agent.router)
app.include_router(reports.router)
app.include_router(predictions.router)
app.include_router(coverage.router)
app.include_router(pipeline.router)
app.include_router(response.router)


@app.get("/", tags=["root"])
def root() -> dict:
    return {
        "name": settings.app_name,
        "version": __version__,
        "environment": settings.app_env,
        "docs": "/docs",
    }