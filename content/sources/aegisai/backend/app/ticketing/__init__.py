"""Ticketing / SOAR abstraction (Phase 18.7 / 18.8).

Provider-agnostic ticket creation + investigation/report export. Defaults to a
credential-free MockProvider; Jira / TheHive / Shuffle (incl. webhook) activate
via environment config. No provider needs to be live for tests.
"""

from backend.app.ticketing.service import (  # noqa: F401
    create_ticket,
    execute_action,
    export_investigation,
    export_report,
    get_provider,
)
