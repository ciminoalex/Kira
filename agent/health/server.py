"""
Server HTTP minimale per esporre l'endpoint /health.
Gira come task asincrono accanto all'agente.
"""

from __future__ import annotations

import json
import logging
from aiohttp import web

from agent.health.checks import run_health_checks

logger = logging.getLogger(__name__)


async def health_handler(request: web.Request) -> web.Response:
    """GET /health — Stato di tutti i servizi."""
    report = await run_health_checks()
    status_code = 200 if report.overall else 503
    return web.json_response(report.to_dict(), status=status_code)


async def start_health_server(host: str = "0.0.0.0", port: int = 8080) -> web.AppRunner:
    """Avvia il server health check."""
    app = web.Application()
    app.router.add_get("/health", health_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()

    logger.info("Health check server avviato su %s:%d", host, port)
    return runner
