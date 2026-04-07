"""
Entry point dell'agente Kira.
Gestisce il routing dei modelli e il lifecycle dell'agente.
"""

from __future__ import annotations

import asyncio
import logging
import signal

from agent.config import settings
from agent.kira_agent import start_agent_with_mcp, stop_mcp_tools
from agent.router.complexity_classifier import classify_complexity, ModelTier
from agent.router.model_registry import get_model_for_tier
from agent.scheduler.jobs import setup_scheduler

logger = logging.getLogger(__name__)

# Stato globale dell'agente (inizializzato in main)
_agent = None
_mcp_tools = None


async def handle_request(user_message: str, user_id: str = "alessandro") -> str:
    """
    Pipeline principale: classifica → routing → esecuzione.

    Args:
        user_message: Messaggio dell'utente
        user_id: ID utente per la sessione

    Returns:
        Risposta testuale dell'agente
    """
    global _agent

    if _agent is None:
        raise RuntimeError("Agente non inizializzato. Chiama init_agent() prima.")

    # 1. Classifica la complessità
    classification = await classify_complexity(user_message)
    logger.info(
        "Classificazione: tier=%s, confidence=%.2f, reason=%s",
        classification.tier.value,
        classification.confidence,
        classification.reason,
    )

    # 2. Se è un task di coding, delega a Claude Code CLI
    if classification.tier == ModelTier.CODE:
        from agent.tools.claude_code import execute_claude_code
        return await execute_claude_code(prompt=user_message)

    # 3. Seleziona il modello e esegui
    model = get_model_for_tier(classification.tier)
    if model:
        _agent.model = model

    response = await _agent.arun(user_message, user_id=user_id)
    return response.content


async def init_agent() -> None:
    """Inizializza l'agente e connette i server MCP."""
    global _agent, _mcp_tools
    _agent, _mcp_tools = await start_agent_with_mcp()
    logger.info("Agente Kira inizializzato con %d MCP tools", len(_mcp_tools))


async def shutdown_agent() -> None:
    """Shutdown pulito dell'agente."""
    global _mcp_tools
    if _mcp_tools:
        await stop_mcp_tools(_mcp_tools)
        logger.info("MCP tools disconnessi")


def get_agent():
    """Restituisce l'istanza dell'agente (per uso diretto dal bot)."""
    return _agent


async def main():
    """Entry point standalone per test dell'agente."""
    from agent.logging_config import setup_logging

    setup_logging(level="INFO", json_format=False)

    logger.info("Avvio Kira...")
    await init_agent()

    # Avvia scheduler
    setup_scheduler()
    logger.info("Scheduler avviato")

    # Avvia health check server
    health_runner = None
    try:
        from agent.health.server import start_health_server

        health_runner = await start_health_server(port=8080)
    except Exception:
        logger.warning("Health check server non avviato", exc_info=True)

    # Mantieni il processo attivo
    stop_event = asyncio.Event()

    def _signal_handler():
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    logger.info("Kira è pronta. In attesa di richieste...")

    try:
        await stop_event.wait()
    finally:
        logger.info("Shutdown in corso...")
        if health_runner:
            await health_runner.cleanup()
        await shutdown_agent()
        logger.info("Kira spenta.")


if __name__ == "__main__":
    asyncio.run(main())
