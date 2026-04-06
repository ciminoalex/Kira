"""
Job schedulati: briefing mattutino, reminder appuntamenti, polling calendari.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from agent.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def morning_briefing() -> None:
    """
    Briefing mattutino: controlla calendari, email non lette, scadenze.
    Invia risultato via Telegram.
    """
    from agent.main import handle_request

    try:
        response = await handle_request(
            "È mattina. Prepara il briefing giornaliero per Alessandro:\n"
            "1. Elenca tutti gli appuntamenti di oggi da ENTRAMBI i calendari "
            "(Gmail personale + Outlook aziendale) in ordine cronologico\n"
            "2. Segnala eventuali conflitti\n"
            "3. Riassumi le email non lette importanti (sia Gmail che Outlook)\n"
            "4. Ricorda scadenze o task pendenti dalla memoria\n"
            "Sii concisa ma completa.",
        )
        await _send_telegram(response)
    except Exception:
        logger.exception("Errore nel briefing mattutino")


async def calendar_poll() -> None:
    """
    Polling calendari ogni 15 minuti.
    Controlla appuntamenti imminenti e invia reminder.
    """
    from agent.main import handle_request

    try:
        response = await handle_request(
            "Controlla se nei prossimi 20 minuti ci sono appuntamenti "
            "su uno dei due calendari (Gmail o Outlook). "
            "Se sì, inviami un reminder breve con titolo, ora e luogo. "
            "Se non ci sono, rispondi solo 'Nessun appuntamento imminente.'",
        )
        # Invia solo se c'è qualcosa di utile
        if response and "nessun" not in response.lower():
            await _send_telegram(f"*Reminder*\n\n{response}")
    except Exception:
        logger.exception("Errore nel polling calendari")


async def check_reminders() -> None:
    """Controlla e notifica i reminder scaduti."""
    from agent.tools.reminder import get_due_reminders

    try:
        result = await get_due_reminders()
        if result and "nessun" not in result.lower():
            await _send_telegram(f"*Reminder*\n\n{result}")
    except Exception:
        logger.exception("Errore nel check reminder")


async def _send_telegram(text: str) -> None:
    """Invia un messaggio Telegram a tutti gli utenti autorizzati."""
    from telegram_bot.bot import bot

    for uid_str in settings.TELEGRAM_ALLOWED_USER_IDS.split(","):
        uid = uid_str.strip()
        if uid:
            try:
                await bot.send_message(
                    chat_id=int(uid),
                    text=text,
                    parse_mode="Markdown",
                )
            except Exception:
                logger.exception("Errore invio Telegram a %s", uid)


def setup_scheduler() -> None:
    """Configura e avvia lo scheduler."""
    hour, minute = settings.BRIEFING_TIME.split(":")

    # Briefing mattutino
    scheduler.add_job(
        morning_briefing,
        CronTrigger(
            hour=int(hour),
            minute=int(minute),
            timezone="Europe/Rome",
        ),
        id="morning_briefing",
        name="Briefing mattutino",
        replace_existing=True,
    )

    # Polling calendari ogni 15 minuti (7:00 - 22:00)
    scheduler.add_job(
        calendar_poll,
        IntervalTrigger(minutes=15),
        id="calendar_poll",
        name="Calendar polling",
        replace_existing=True,
    )

    # Check reminder ogni 5 minuti
    scheduler.add_job(
        check_reminders,
        IntervalTrigger(minutes=5),
        id="check_reminders",
        name="Reminder check",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler avviato con %d job", len(scheduler.get_jobs()))
