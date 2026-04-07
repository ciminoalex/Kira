"""
Test per il classificatore di complessità e il model registry.
"""

import pytest
from unittest.mock import patch, AsyncMock

from agent.router.complexity_classifier import (
    classify_complexity,
    ModelTier,
    ClassificationResult,
)
from agent.router.model_registry import get_model_for_tier, get_fallback_for_tier


@pytest.mark.asyncio
async def test_classify_greeting_as_fast():
    """Saluti devono essere classificati come FAST."""
    result = await classify_complexity("Ciao!")
    assert result.tier == ModelTier.FAST

    result = await classify_complexity("Buongiorno")
    assert result.tier == ModelTier.FAST

    result = await classify_complexity("Grazie!")
    assert result.tier == ModelTier.FAST


@pytest.mark.asyncio
async def test_classify_email_as_standard():
    """Lettura email deve essere STANDARD."""
    result = await classify_complexity("Leggi le mie mail")
    assert result.tier == ModelTier.STANDARD


@pytest.mark.asyncio
async def test_classify_reminder_as_standard():
    """Reminder deve essere STANDARD."""
    result = await classify_complexity("Ricordami di chiamare Marco")
    assert result.tier == ModelTier.STANDARD


@pytest.mark.asyncio
async def test_classify_coding_as_code():
    """Richieste di coding devono essere CODE."""
    result = await classify_complexity("Fixa il bug nel file main.py")
    assert result.tier == ModelTier.CODE

    result = await classify_complexity("Scrivi una funzione Python per ordinare")
    assert result.tier == ModelTier.CODE


@pytest.mark.asyncio
async def test_classify_strategy_as_expert():
    """Analisi strategiche devono essere EXPERT."""
    result = await classify_complexity("Valuta i pro e contro di migrare a HANA")
    assert result.tier == ModelTier.EXPERT


@pytest.mark.asyncio
async def test_classify_ambiguous_falls_back():
    """Messaggi ambigui devono fare fallback su ADVANCED."""
    result = await classify_complexity("Che ne pensi di questa idea?")
    assert result.tier == ModelTier.ADVANCED
    assert "fallback" in result.reason.lower()


def test_get_model_for_code_tier():
    """Il tier CODE deve restituire None (gestito da CLI)."""
    model = get_model_for_tier(ModelTier.CODE)
    assert model is None


def test_get_model_for_standard_tier():
    """Il tier STANDARD deve restituire un modello valido."""
    model = get_model_for_tier(ModelTier.STANDARD)
    assert model is not None


def test_get_fallback_for_code_tier():
    """Il fallback per CODE deve essere Sonnet."""
    model = get_fallback_for_tier(ModelTier.CODE)
    assert model is not None
