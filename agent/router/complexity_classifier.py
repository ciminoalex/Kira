"""
Classifica la complessità di una richiesta utente per selezionare
il modello appropriato.

Usa pattern matching euristico (zero latenza).
Per messaggi ambigui, fallback su tier ADVANCED (Sonnet).
"""

from __future__ import annotations

import re
import logging
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    FAST = "fast"          # Haiku (saluti, conferme)
    STANDARD = "standard"  # Haiku (email, reminder)
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
    r"^(ciao|buongiorno|buonasera|hey|ok|grazie|perfetto|va bene|sì|no)(\s+\w+)?[\s!?.]*$",
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
    """Classifica la complessità di un messaggio tramite pattern matching."""
    message_lower = message.lower().strip()

    # Pattern matching euristico (zero latenza)
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

    # Messaggi ambigui → Sonnet (safe default)
    return ClassificationResult(
        tier=ModelTier.ADVANCED,
        confidence=0.5,
        reason="Nessun pattern match, fallback su ADVANCED",
    )
