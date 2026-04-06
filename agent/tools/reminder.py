"""
Tool Agno per gestire i reminder (CRUD) via PostgreSQL.
"""

from __future__ import annotations

import logging
from datetime import datetime

import asyncpg
from agno.tools import tool

from agent.config import settings

logger = logging.getLogger(__name__)


async def _get_connection() -> asyncpg.Connection:
    return await asyncpg.connect(settings.async_db_url)


@tool(name="create_reminder", description=(
    "Crea un nuovo reminder/promemoria. "
    "Parametri: title (str), due_at (ISO datetime), "
    "description (str, opzionale), recurrence ('daily'|'weekly'|'monthly'|null)."
))
async def create_reminder(
    title: str,
    due_at: str,
    description: str = "",
    recurrence: str | None = None,
) -> str:
    """Crea un nuovo reminder nel database."""
    conn = await _get_connection()
    try:
        due = datetime.fromisoformat(due_at)
        row = await conn.fetchrow(
            """
            INSERT INTO reminders (title, description, due_at, recurrence)
            VALUES ($1, $2, $3, $4)
            RETURNING id, title, due_at
            """,
            title, description, due, recurrence,
        )
        return (
            f"Reminder creato (ID: {row['id']}): "
            f"'{row['title']}' per {row['due_at'].strftime('%d/%m/%Y %H:%M')}"
        )
    except Exception as e:
        logger.exception("Errore creazione reminder")
        return f"Errore nella creazione del reminder: {e}"
    finally:
        await conn.close()


@tool(name="list_reminders", description=(
    "Elenca i reminder attivi (non ancora notificati). "
    "Parametro opzionale: limit (int, default 10)."
))
async def list_reminders(limit: int = 10) -> str:
    """Elenca i prossimi reminder."""
    conn = await _get_connection()
    try:
        rows = await conn.fetch(
            """
            SELECT id, title, due_at, recurrence
            FROM reminders
            WHERE notified = FALSE AND due_at >= NOW()
            ORDER BY due_at ASC
            LIMIT $1
            """,
            limit,
        )
        if not rows:
            return "Nessun reminder attivo."
        lines = []
        for r in rows:
            rec = f" ({r['recurrence']})" if r['recurrence'] else ""
            lines.append(
                f"- [{r['id']}] {r['title']} — "
                f"{r['due_at'].strftime('%d/%m/%Y %H:%M')}{rec}"
            )
        return "Reminder attivi:\n" + "\n".join(lines)
    finally:
        await conn.close()


@tool(name="delete_reminder", description=(
    "Elimina un reminder per ID."
))
async def delete_reminder(reminder_id: int) -> str:
    """Elimina un reminder dal database."""
    conn = await _get_connection()
    try:
        result = await conn.execute(
            "DELETE FROM reminders WHERE id = $1", reminder_id
        )
        if result == "DELETE 1":
            return f"Reminder {reminder_id} eliminato."
        return f"Reminder {reminder_id} non trovato."
    finally:
        await conn.close()


@tool(name="get_due_reminders", description=(
    "Recupera i reminder scaduti/in scadenza che non sono ancora stati notificati."
))
async def get_due_reminders() -> str:
    """Recupera i reminder da notificare."""
    conn = await _get_connection()
    try:
        rows = await conn.fetch(
            """
            SELECT id, title, description, due_at
            FROM reminders
            WHERE notified = FALSE AND due_at <= NOW()
            ORDER BY due_at ASC
            """
        )
        if not rows:
            return "Nessun reminder scaduto."

        # Segna come notificati
        ids = [r["id"] for r in rows]
        await conn.execute(
            "UPDATE reminders SET notified = TRUE WHERE id = ANY($1::int[])",
            ids,
        )

        lines = []
        for r in rows:
            desc = f" — {r['description']}" if r["description"] else ""
            lines.append(f"- {r['title']}{desc}")
        return "Reminder scaduti:\n" + "\n".join(lines)
    finally:
        await conn.close()
