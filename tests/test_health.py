"""
Test per il sistema di health check (Phase 4).
"""

import pytest
from unittest.mock import patch, AsyncMock

from agent.health.checks import (
    ServiceStatus,
    HealthReport,
    check_ollama,
    run_health_checks,
)


def test_health_report_healthy():
    """Report con PostgreSQL healthy deve essere overall healthy."""
    report = HealthReport(
        services=[
            ServiceStatus("postgres", True, 5.0),
            ServiceStatus("ollama", False, error="Non raggiungibile"),
        ]
    )
    d = report.to_dict()
    assert d["status"] == "healthy"
    assert d["services"]["postgres"]["healthy"]
    assert not d["services"]["ollama"]["healthy"]


def test_health_report_degraded():
    """Report senza PostgreSQL healthy deve essere degraded."""
    report = HealthReport(
        overall=False,
        services=[
            ServiceStatus("postgres", False, error="Connection refused"),
            ServiceStatus("ollama", True, 10.0),
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
async def test_check_ollama_unreachable():
    """Se Ollama non è raggiungibile, deve restituire unhealthy."""
    with patch("agent.health.checks.httpx.AsyncClient") as mock:
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Connection refused")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock.return_value = mock_client

        result = await check_ollama()
        assert not result.healthy
        assert result.error is not None
