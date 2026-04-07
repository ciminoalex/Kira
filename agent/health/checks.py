"""
Health check per tutti i servizi di Kira.
Espone un endpoint HTTP /health per monitoraggio uptime.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime

import asyncpg
import httpx

from agent.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ServiceStatus:
    name: str
    healthy: bool
    latency_ms: float = 0.0
    error: str | None = None


@dataclass
class HealthReport:
    timestamp: datetime = field(default_factory=datetime.utcnow)
    overall: bool = True
    services: list[ServiceStatus] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "status": "healthy" if self.overall else "degraded",
            "timestamp": self.timestamp.isoformat(),
            "services": {
                s.name: {
                    "healthy": s.healthy,
                    "latency_ms": round(s.latency_ms, 1),
                    **({"error": s.error} if s.error else {}),
                }
                for s in self.services
            },
        }


async def check_postgres() -> ServiceStatus:
    """Verifica connessione PostgreSQL."""
    try:
        start = asyncio.get_event_loop().time()
        conn = await asyncio.wait_for(
            asyncpg.connect(settings.async_db_url), timeout=5.0
        )
        await conn.execute("SELECT 1")
        await conn.close()
        latency = (asyncio.get_event_loop().time() - start) * 1000
        return ServiceStatus("postgres", True, latency)
    except Exception as e:
        return ServiceStatus("postgres", False, error=str(e))


async def check_ollama() -> ServiceStatus:
    """Verifica connessione Ollama (modello locale)."""
    try:
        start = asyncio.get_event_loop().time()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=3.0
            )
            latency = (asyncio.get_event_loop().time() - start) * 1000
            return ServiceStatus("ollama", resp.status_code == 200, latency)
    except Exception as e:
        return ServiceStatus("ollama", False, error=str(e))


async def check_supermemory() -> ServiceStatus:
    """Verifica connessione Supermemory."""
    if not settings.SUPERMEMORY_API_KEY:
        return ServiceStatus("supermemory", False, error="Non configurato")
    try:
        start = asyncio.get_event_loop().time()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.supermemory.ai/v3/health",
                headers={"Authorization": f"Bearer {settings.SUPERMEMORY_API_KEY}"},
                timeout=5.0,
            )
            latency = (asyncio.get_event_loop().time() - start) * 1000
            return ServiceStatus("supermemory", resp.status_code == 200, latency)
    except Exception as e:
        return ServiceStatus("supermemory", False, error=str(e))


async def check_pc_filesystem() -> ServiceStatus:
    """Verifica connessione al PC fisso via Tailscale."""
    if not settings.PC_TAILSCALE_IP:
        return ServiceStatus("pc_filesystem", False, error="Non configurato")
    try:
        url = f"http://{settings.PC_TAILSCALE_IP}:{settings.PC_FILESYSTEM_PORT}/health"
        start = asyncio.get_event_loop().time()
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=3.0)
            latency = (asyncio.get_event_loop().time() - start) * 1000
            return ServiceStatus("pc_filesystem", resp.status_code == 200, latency)
    except Exception:
        return ServiceStatus("pc_filesystem", False, error="PC offline")


async def run_health_checks() -> HealthReport:
    """Esegue tutti gli health check in parallelo."""
    checks = await asyncio.gather(
        check_postgres(),
        check_ollama(),
        check_supermemory(),
        check_pc_filesystem(),
        return_exceptions=True,
    )

    services = []
    for result in checks:
        if isinstance(result, Exception):
            services.append(ServiceStatus("unknown", False, error=str(result)))
        else:
            services.append(result)

    # Overall healthy se PostgreSQL (critico) è up
    postgres_healthy = any(s.name == "postgres" and s.healthy for s in services)

    return HealthReport(
        overall=postgres_healthy,
        services=services,
    )
