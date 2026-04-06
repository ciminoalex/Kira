"""
Handler per i comandi Telegram: /start, /briefing, /remind, /memory
"""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from agent.main import handle_request

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Ciao Alessandro! Sono Kira, la tua assistente personale.\n\n"
        "Puoi scrivermi o inviarmi messaggi vocali. Ecco i comandi disponibili:\n"
        "/briefing — Briefing della giornata\n"
        "/remind — Gestisci i tuoi reminder\n"
        "/memory — Cerca nella mia memoria\n"
    )


@router.message(Command("briefing"))
async def cmd_briefing(message: Message) -> None:
    await message.chat.do("typing")
    response = await handle_request(
        "Fammi il briefing della giornata: controlla entrambi i calendari "
        "(Gmail e Outlook), elenca gli appuntamenti in ordine cronologico, "
        "segnala conflitti, e riassumi le email importanti non lette.",
    )
    await message.answer(response, parse_mode="Markdown")


@router.message(Command("remind"))
async def cmd_remind(message: Message) -> None:
    await message.chat.do("typing")
    response = await handle_request("Elenca i miei reminder attivi.")
    await message.answer(response, parse_mode="Markdown")


@router.message(Command("memory"))
async def cmd_memory(message: Message) -> None:
    """Cerca nella memoria. Uso: /memory <query>"""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Uso: /memory <cosa cercare>\n"
            "Esempio: /memory progetto NCO"
        )
        return

    query = args[1]
    await message.chat.do("typing")
    response = await handle_request(
        f"Cerca nella tua memoria informazioni su: {query}"
    )
    await message.answer(response, parse_mode="Markdown")
