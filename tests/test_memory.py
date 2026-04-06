"""
Test per il wrapper Supermemory.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def memory_manager():
    with patch("agent.memory.supermemory_wrapper.AsyncSupermemory") as mock_cls:
        mock_client = MagicMock()
        mock_client.memories = MagicMock()
        mock_client.memories.add = AsyncMock()
        mock_client.search = MagicMock()
        mock_client.search.memories = AsyncMock(return_value={"results": []})
        mock_client.profile = AsyncMock(return_value={})
        mock_cls.return_value = mock_client

        from agent.memory.supermemory_wrapper import SupermemoryManager

        manager = SupermemoryManager(
            api_key="test_key",
            container_tag="test_container",
        )
        manager.client = mock_client
        yield manager


@pytest.mark.asyncio
async def test_remember(memory_manager):
    """Deve salvare un fatto in memoria."""
    await memory_manager.remember("Alessandro lavora a Vasto")
    memory_manager.client.memories.add.assert_called_once()
    call_kwargs = memory_manager.client.memories.add.call_args
    assert "Alessandro lavora a Vasto" in str(call_kwargs)


@pytest.mark.asyncio
async def test_recall(memory_manager):
    """Deve cercare nella memoria."""
    await memory_manager.recall("dove lavora Alessandro")
    memory_manager.client.search.memories.assert_called_once()


@pytest.mark.asyncio
async def test_get_profile(memory_manager):
    """Deve recuperare il profilo utente."""
    await memory_manager.get_profile()
    memory_manager.client.profile.assert_called_once()


@pytest.mark.asyncio
async def test_add_conversation(memory_manager):
    """Deve salvare una conversazione come memoria."""
    await memory_manager.add_conversation(
        "Ciao Kira", "Ciao Alessandro!"
    )
    memory_manager.client.memories.add.assert_called_once()
    call_kwargs = memory_manager.client.memories.add.call_args
    assert "User: Ciao Kira" in str(call_kwargs)
    assert "Assistant: Ciao Alessandro!" in str(call_kwargs)


@pytest.mark.asyncio
async def test_remember_error_handling(memory_manager):
    """Deve gestire errori senza propagarli."""
    memory_manager.client.memories.add.side_effect = Exception("API error")
    # Non deve lanciare eccezioni
    await memory_manager.remember("test")


@pytest.mark.asyncio
async def test_recall_error_handling(memory_manager):
    """Deve restituire dict vuoto in caso di errore."""
    memory_manager.client.search.memories.side_effect = Exception("API error")
    result = await memory_manager.recall("test")
    assert result == {}
