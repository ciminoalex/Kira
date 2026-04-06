"""
Speech-to-Text via Deepgram Nova-2.
Supporta italiano e inglese.
"""

from __future__ import annotations

import logging

from deepgram import DeepgramClient, PrerecordedOptions

from agent.config import settings

logger = logging.getLogger(__name__)


async def transcribe_voice(audio_bytes: bytes, language: str = "it") -> str:
    """
    Trascrivi audio in testo usando Deepgram Nova-2.

    Args:
        audio_bytes: Audio in formato OGG/Opus (come da Telegram)
        language: Lingua ('it' per italiano, 'en' per inglese)

    Returns:
        Testo trascritto
    """
    client = DeepgramClient(settings.DEEPGRAM_API_KEY)

    options = PrerecordedOptions(
        model="nova-2",
        language=language,
        smart_format=True,
        punctuate=True,
    )

    source = {"buffer": audio_bytes, "mimetype": "audio/ogg"}

    try:
        response = await client.listen.asyncrest.v("1").transcribe_file(
            source, options
        )
        transcript = (
            response.results.channels[0].alternatives[0].transcript
        )
        logger.info("Trascritto: %s", transcript[:80])
        return transcript
    except Exception:
        logger.exception("Errore trascrizione Deepgram")
        return ""
