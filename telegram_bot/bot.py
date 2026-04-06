"""
Telegram bot per interagire con Kira via testo e vocali.
Usa aiogram 3.x.
"""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Message

from agent.config import settings
from agent.main import init_agent, shutdown_agent
from telegram_bot.handlers import commands, text, voice

logger = logging.getLogger(__name__)

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Registra i router dei handler
dp.include_router(commands.router)
dp.include_router(voice.router)
dp.include_router(text.router)  # Deve essere l'ultimo (catch-all per F.text)

# Set di user ID autorizzati
ALLOWED_USERS: set[int] = set()


def _parse_allowed_users() -> set[int]:
    """Parsa la lista di user ID autorizzati dalla configurazione."""
    if not settings.TELEGRAM_ALLOWED_USER_IDS:
        return set()
    return {
        int(uid.strip())
        for uid in settings.TELEGRAM_ALLOWED_USER_IDS.split(",")
        if uid.strip()
    }


@dp.message.outer_middleware()
async def auth_middleware(handler, event: Message, data: dict):
    """Middleware di autenticazione: solo utenti autorizzati."""
    if not ALLOWED_USERS or (
        event.from_user and event.from_user.id in ALLOWED_USERS
    ):
        return await handler(event, data)

    logger.warning(
        "Accesso negato per user_id=%s (%s)",
        event.from_user.id if event.from_user else "unknown",
        event.from_user.username if event.from_user else "unknown",
    )
    return None  # Ignora silenziosamente


async def main():
    """Entry point del bot Telegram."""
    global ALLOWED_USERS

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    ALLOWED_USERS = _parse_allowed_users()
    logger.info("Utenti autorizzati: %s", ALLOWED_USERS)

    # Inizializza l'agente
    logger.info("Inizializzazione agente Kira...")
    await init_agent()

    # Avvia scheduler
    from agent.scheduler.jobs import setup_scheduler
    setup_scheduler()
    logger.info("Scheduler avviato")

    # Avvia il polling
    logger.info("Bot Telegram in ascolto...")
    try:
        await dp.start_polling(bot)
    finally:
        await shutdown_agent()


if __name__ == "__main__":
    asyncio.run(main())
