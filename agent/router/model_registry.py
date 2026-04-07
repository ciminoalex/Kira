"""
Registry dei modelli disponibili con configurazione e fallback chain.
"""

from __future__ import annotations

from agno.models.anthropic import Claude

from agent.router.complexity_classifier import ModelTier


MODEL_CONFIG: dict[ModelTier, dict] = {
    ModelTier.FAST: {
        "primary": Claude(id="claude-haiku-4-5-20251001"),
        "fallback": Claude(id="claude-haiku-4-5-20251001"),
        "max_tokens": 512,
        "description": "Risposte rapide, small talk, conferme",
    },
    ModelTier.STANDARD: {
        "primary": Claude(id="claude-haiku-4-5-20251001"),
        "fallback": Claude(id="claude-sonnet-4-6"),
        "max_tokens": 2048,
        "description": "Lettura email, reminder, domande fattuali",
    },
    ModelTier.ADVANCED: {
        "primary": Claude(id="claude-sonnet-4-6"),
        "fallback": Claude(id="claude-sonnet-4-6"),
        "max_tokens": 4096,
        "description": "Analisi, briefing, redazione, pianificazione",
    },
    ModelTier.EXPERT: {
        "primary": Claude(id="claude-opus-4-6"),
        "fallback": Claude(id="claude-sonnet-4-6"),
        "max_tokens": 8192,
        "description": "Ragionamento complesso, documenti strategici",
    },
}


def get_model_for_tier(tier: ModelTier):
    """Restituisce il modello primario per il tier dato."""
    if tier == ModelTier.CODE:
        return None  # Gestito via Claude Code CLI tool
    return MODEL_CONFIG[tier]["primary"]


def get_fallback_for_tier(tier: ModelTier):
    """Restituisce il modello fallback."""
    if tier == ModelTier.CODE:
        return Claude(id="claude-sonnet-4-6")
    return MODEL_CONFIG[tier]["fallback"]
