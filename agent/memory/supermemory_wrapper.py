"""
Wrapper Python per Supermemory API.
Usato dallo scheduler e dal bot per operazioni di memoria dirette
(senza passare dall'agente).
"""

from __future__ import annotations

import logging

from supermemory import AsyncSupermemory

logger = logging.getLogger(__name__)


class SupermemoryManager:
    """Gestisce la memoria di Kira via Supermemory API."""

    def __init__(self, api_key: str, container_tag: str = "kira_alessandro"):
        self.client = AsyncSupermemory(api_key=api_key)
        self.container_tag = container_tag

    async def remember(self, content: str, metadata: dict | None = None) -> None:
        """Salva un fatto/informazione nella memoria."""
        try:
            await self.client.memories.add(
                content=content,
                container_tags=[self.container_tag],
                metadata=metadata or {},
            )
            logger.info("Memorizzato: %s", content[:80])
        except Exception:
            logger.exception("Errore nel salvare in memoria")

    async def recall(self, query: str, limit: int = 5) -> dict:
        """Cerca nella memoria + knowledge base (hybrid search)."""
        try:
            return await self.client.search.memories(
                q=query,
                container_tags=[self.container_tag],
                limit=limit,
            )
        except Exception:
            logger.exception("Errore nella ricerca in memoria")
            return {}

    async def get_profile(self, query: str | None = None) -> dict:
        """
        Recupera il profilo utente completo.
        - profile.static: fatti stabili (ruolo, preferenze, progetti)
        - profile.dynamic: contesto recente (attività in corso)
        """
        try:
            return await self.client.profile(
                container_tags=[self.container_tag],
            )
        except Exception:
            logger.exception("Errore nel recupero profilo")
            return {}

    async def add_conversation(
        self, user_message: str, assistant_message: str
    ) -> None:
        """
        Salva una conversazione completa.
        Supermemory estrae automaticamente i fatti rilevanti.
        """
        conversation = f"User: {user_message}\nAssistant: {assistant_message}"
        await self.remember(
            conversation,
            metadata={"type": "conversation"},
        )
