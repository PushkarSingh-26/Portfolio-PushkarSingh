"""Application configuration loaded from environment variables / .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root: backend/app/config.py -> backend/app -> backend -> root
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "cti-platform"
    app_env: str = "development"
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "cti_db"
    postgres_user: str = "cti_user"
    postgres_password: str = "change_me_in_production"
    database_url: str = ""

    # External feeds
    # NVD API key is optional but raises the rate limit from 5 to 50
    # requests per 30-second window. Request one at https://nvd.nist.gov/developers/request-an-api-key
    nvd_api_key: str = ""

    # MISP connection (Phase 9). Provided by the environment / .env.
    misp_url: str = ""
    misp_api_key: str = ""
    misp_ssl_verify: bool = True

    # Wazuh connection (Phase 10). Provided by the environment / .env.
    wazuh_api_url: str = ""
    wazuh_username: str = ""
    wazuh_password: str = ""
    indexer_url: str = ""
    indexer_username: str = ""
    indexer_password: str = ""
    wazuh_verify_ssl: bool = False

    # Neo4j knowledge graph (Phase 11). Provided by the environment / .env.
    neo4j_uri: str = "bolt://127.0.0.1:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "cti_graph_pass"

    # AI Threat Analyst (Phase 13). No provider lock-in; "none" -> deterministic
    # evidence-grounded responses (works with zero LLM credentials).
    ai_provider: str = "none"            # none | gemini | openai | ollama
    ai_model: str = ""                   # provider model id (sensible default per provider)
    ai_temperature: float = 0.1
    gemini_api_key: str = ""
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    ollama_url: str = "http://localhost:11434"

    # Ticketing connectors (Phase 15.6). Default "mock" needs no credentials.
    ticket_provider: str = "mock"        # mock | jira | thehive | shuffle
    jira_url: str = ""
    jira_user: str = ""
    jira_token: str = ""
    jira_project: str = "SOC"
    thehive_url: str = ""
    thehive_api_key: str = ""
    shuffle_url: str = ""
    shuffle_api_key: str = ""
    shuffle_workflow_id: str = ""
    shuffle_webhook_url: str = ""

    # Orchestration (Phase 18). Scheduler is opt-in so tests/dev don't auto-run jobs.
    orchestration_enabled: bool = False
    job_max_retries: int = 2
    job_retry_backoff_seconds: float = 2.0

    # Run Alembic migrations to head on application startup (dev convenience).
    auto_migrate: bool = True

    @property
    def sqlalchemy_database_url(self) -> str:
        """Prefer explicit DATABASE_URL, otherwise build one from parts."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
