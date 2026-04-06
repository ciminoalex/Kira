"""
Handler per messaggi di testo generici (non comandi).
"""

from __future__ import annotations

import logging

from aiogram import Router, F
from aiogram.types import Message

from agent.main import handle_request
from agent.memory.supermemory_wrapper import SupermemoryManager
from agent.config import settings

logger = logging.getLogger(__name__)

router = Router()

_memory_manager: SupermemoryManager | None = None


def _get_memory_manager() -> SupermemoryManager:
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = SupermemoryManager(
            api_key=settings.SUPERMEMORY_API_KEY,
            container_tag=settings.SUPERMEMORY_CONTAINER_TAG,
        )
    return _memory_manager


@router.message(F.text)
async def handle_text(message: Message) -> None:
    """Gestione messaggi testo → agente → risposta."""
    await message.chat.do("typing")

    response = await handle_request(message.text)
    await message.answer(response, parse_mode="Markdown")

    # Salva la conversazione in Supermemory per estrazione fatti automatica
    try:
        memory = _get_memory_manager()
        await memory.add_conversation(message.text, response)
    except Exception:
        logger.debug("Errore salvataggio conversazione in memoria", exc_info=True)
