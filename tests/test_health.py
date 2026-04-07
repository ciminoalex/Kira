"""
Test per il sistema di health check (Phase 4).
"""

import pytest
from unittest.mock import patch, AsyncMock

from agent.health.checks import (
    ServiceStatus,
    HealthReport,
    check_supermemory,
)


def test_health_report_healthy():
    """Report con PostgreSQL healthy deve essere overall healthy."""
    report = HealthReport(
        services=[
            ServiceStatus("postgres", True, 5.0),
            ServiceStatus("supermemory", False, error="Non configurato"),
        ]
    )
    d = report.to_dict()
    assert d["status"] == "healthy"
    assert d["services"]["postgres"]["healthy"]
    assert not d["services"]["supermemory"]["healthy"]


def test_health_report_degraded():
    """Report senza PostgreSQL healthy deve essere degraded."""
    report = HealthReport(
        overall=False,
        services=[
            ServiceStatus("postgres", False, error="Connection refused"),
            ServiceStatus("supermemory", True, 10.0),
        ],
    )
    d = report.to_dict()
    assert d["status"] == "degraded"


def test_service_status_without_error():
    """ServiceStatus senza errore non deve includere campo error."""
    s = ServiceStatus("test", True, 1.5)
    report = HealthReport(services=[s])
    d = report.to_dict()
    assert "error" not in d["services"]["test"]


@pytest.mark.asyncio
async def test_check_supermemory_not_configured():
    """Se Supermemory non è configurato, deve restituire unhealthy."""
    with patch("agent.health.checks.settings") as mock_settings:
        mock_settings.SUPERMEMORY_API_KEY = ""
        result = await check_supermemory()
        assert not result.healthy
        assert "Non configurato" in result.error
