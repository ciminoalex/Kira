"""
Classifica la complessità di una richiesta utente per selezionare
il modello appropriato.

Livello 1: Pattern matching euristico (zero latenza)
Livello 2: Se ambiguo, usa Gemma locale via Ollama (~200ms)
Livello 3: Fallback su tier ADVANCED (Sonnet)
"""

from __future__ import annotations

import re
import logging
from enum import Enum
from dataclasses import dataclass

import httpx

from agent.config import settings

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    FAST = "fast"          # Gemma 4 locale
    STANDARD = "standard"  # Haiku
    ADVANCED = "advanced"  # Sonnet
    EXPERT = "expert"      # Opus
    CODE = "code"          # Claude Code CLI


@dataclass
class ClassificationResult:
    tier: ModelTier
    confidence: float
    reason: str


# --- Pattern euristici ---

FAST_PATTERNS = [
    r"^(ciao|buongiorno|buonasera|hey|ok|grazie|perfetto|va bene|sì|no)[\s!?.]*$",
    r"^(conferm|ok|fatto|ricevuto|capito)",
    r"che ore sono|che giorno è",
]

STANDARD_PATTERNS = [
    r"ricordami|reminder|promemoria",
    r"(leggi|mostra|elenca).*(mail|email|calendario|appuntament)",
    r"^(chi è|cos'è|quando è|dove si trova|qual è)",
]

ADVANCED_PATTERNS = [
    r"(fammi|prepara|genera).*(briefing|riassunto|report|sommario)",
    r"(scrivi|redigi|componi).*(email|mail|messaggio|lettera)",
    r"(pianifica|organizza|programma)",
]

CODE_PATTERNS = [
    r"(scrivi|crea|modifica|fix|debug|refactor).*(codice|script|funzione|classe|file|bug)",
    r"(commit|push|pull request|deploy|test|build)",
    r"\.(py|js|ts|cs|sql|sh|yaml|json|xml)\b",
    r"(analizza|revisiona|ottimizza).*(codice|codebase|repository|repo)",
]

EXPERT_PATTERNS = [
    r"(strategia|valuta|confronta|pro e contro|analisi approfondita)",
    r"(relazione tecnica|business plan|proposta commerciale|documentazione R&S)",
]


async def classify_complexity(
    message: str,
    conversation_history: list[dict] | None = None,
) -> ClassificationResult:
    """Classifica la complessità di un messaggio."""
    message_lower = message.lower().strip()

    # Livello 1: Pattern matching
    pattern_checks = [
        (FAST_PATTERNS, ModelTier.FAST, 0.9, "saluto/conferma"),
        (CODE_PATTERNS, ModelTier.CODE, 0.85, "richiesta coding"),
        (EXPERT_PATTERNS, ModelTier.EXPERT, 0.8, "task complesso"),
        (STANDARD_PATTERNS, ModelTier.STANDARD, 0.85, "task standard"),
        (ADVANCED_PATTERNS, ModelTier.ADVANCED, 0.85, "task avanzato"),
    ]

    for patterns, tier, confidence, reason in pattern_checks:
        for pattern in patterns:
            if re.search(pattern, message_lower):
                return ClassificationResult(
                    tier=tier,
                    confidence=confidence,
                    reason=f"Pattern match: {reason}",
                )

    # Livello 2: Classificazione con modello locale (Ollama)
    return await _classify_with_local_model(message)


async def _classify_with_local_model(message: str) -> ClassificationResult:
    """Usa Gemma locale (via Ollama) per classificare messaggi ambigui."""
    prompt = (
        "Classifica questa richiesta utente in una di queste categorie:\n"
        "- FAST: saluti, conferme, domande banali\n"
        "- STANDARD: lettura email/calendario, reminder, domande fattuali\n"
        "- ADVANCED: analisi, pianificazione, redazione, briefing\n"
        "- EXPERT: ragionamento complesso, decisioni strategiche, documenti formali\n"
        "- CODE: qualsiasi cosa riguardi codice, programmazione, debug, file editing\n\n"
        f'Richiesta: "{message}"\n\n'
        "Rispondi SOLO con il nome della categoria (FAST/STANDARD/ADVANCED/EXPERT/CODE)."
    )

    tier_map = {
        "FAST": ModelTier.FAST,
        "STANDARD": ModelTier.STANDARD,
        "ADVANCED": ModelTier.ADVANCED,
        "EXPERT": ModelTier.EXPERT,
        "CODE": ModelTier.CODE,
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={"model": "gemma3:27b", "prompt": prompt, "stream": False},
                timeout=5.0,
            )
            result = resp.json()["response"].strip().upper()
            # Estrai solo la prima parola (in caso di output verboso)
            first_word = result.split()[0] if result else "ADVANCED"
            tier = tier_map.get(first_word, ModelTier.ADVANCED)
            return ClassificationResult(
                tier=tier,
                confidence=0.7,
                reason=f"Classificato da Gemma locale: {first_word}",
            )
    except Exception:
        logger.debug("Ollama non raggiungibile, fallback su ADVANCED")
        return ClassificationResult(
            tier=ModelTier.ADVANCED,
            confidence=0.5,
            reason="Fallback: Ollama non raggiungibile",
        )
