"""
Tool Agno per gestire le note/appunti via PostgreSQL.
"""

from __future__ import annotations

import logging

import asyncpg
from agno.tools import tool

from agent.config import settings

logger = logging.getLogger(__name__)


async def _get_connection() -> asyncpg.Connection:
    return await asyncpg.connect(settings.async_db_url)


@tool(name="save_note", description=(
    "Salva una nota/appunto. Parametri: title (str), content (str), "
    "tags (list[str], opzionale)."
))
async def save_note(
    title: str,
    content: str,
    tags: list[str] | None = None,
) -> str:
    """Salva una nuova nota."""
    conn = await _get_connection()
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO notes (title, content, tags)
            VALUES ($1, $2, $3)
            RETURNING id, title
            """,
            title, content, tags or [],
        )
        return f"Nota salvata (ID: {row['id']}): '{row['title']}'"
    except Exception as e:
        logger.exception("Errore salvataggio nota")
        return f"Errore nel salvataggio: {e}"
    finally:
        await conn.close()


@tool(name="search_notes", description=(
    "Cerca nelle note per testo o tag. Parametri: query (str), limit (int, default 5)."
))
async def search_notes(query: str, limit: int = 5) -> str:
    """Cerca nelle note con ricerca full-text."""
    conn = await _get_connection()
    try:
        rows = await conn.fetch(
            """
            SELECT id, title, content, tags, created_at
            FROM notes
            WHERE to_tsvector('italian', title || ' ' || content) @@
                  plainto_tsquery('italian', $1)
               OR $1 = ANY(tags)
            ORDER BY created_at DESC
            LIMIT $2
            """,
            query, limit,
        )
        if not rows:
            return f"Nessuna nota trovata per '{query}'."
        lines = []
        for r in rows:
            tag_str = f" [{', '.join(r['tags'])}]" if r["tags"] else ""
            lines.append(
                f"- [{r['id']}] **{r['title']}**{tag_str}\n  {r['content'][:120]}..."
            )
        return "Note trovate:\n" + "\n".join(lines)
    finally:
        await conn.close()


@tool(name="list_notes", description=(
    "Elenca le note più recenti. Parametro: limit (int, default 10)."
))
async def list_notes(limit: int = 10) -> str:
    """Elenca le note più recenti."""
    conn = await _get_connection()
    try:
        rows = await conn.fetch(
            """
            SELECT id, title, tags, created_at
            FROM notes
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit,
        )
        if not rows:
            return "Nessuna nota presente."
        lines = []
        for r in rows:
            tag_str = f" [{', '.join(r['tags'])}]" if r["tags"] else ""
            lines.append(
                f"- [{r['id']}] {r['title']}{tag_str} "
                f"({r['created_at'].strftime('%d/%m/%Y')})"
            )
        return "Note recenti:\n" + "\n".join(lines)
    finally:
        await conn.close()


@tool(name="delete_note", description="Elimina una nota per ID.")
async def delete_note(note_id: int) -> str:
    """Elimina una nota dal database."""
    conn = await _get_connection()
    try:
        result = await conn.execute("DELETE FROM notes WHERE id = $1", note_id)
        if result == "DELETE 1":
            return f"Nota {note_id} eliminata."
        return f"Nota {note_id} non trovata."
    finally:
        await conn.close()
