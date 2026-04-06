"""
Text-to-Speech via ElevenLabs Turbo v2.
"""

from __future__ import annotations

import logging
from io import BytesIO

from elevenlabs import AsyncElevenLabs

from agent.config import settings

logger = logging.getLogger(__name__)


async def synthesize_speech(text: str) -> BytesIO:
    """
    Sintetizza testo in audio usando ElevenLabs.

    Args:
        text: Testo da sintetizzare

    Returns:
        BytesIO contenente l'audio in formato MP3
    """
    client = AsyncElevenLabs(api_key=settings.ELEVENLABS_API_KEY)

    try:
        audio_generator = await client.text_to_speech.convert(
            voice_id=settings.ELEVENLABS_VOICE_ID,
            text=text,
            model_id="eleven_turbo_v2",
            output_format="mp3_44100_128",
        )

        audio_buffer = BytesIO()
        async for chunk in audio_generator:
            audio_buffer.write(chunk)
        audio_buffer.seek(0)
        audio_buffer.name = "response.mp3"

        logger.info("TTS sintetizzato: %d bytes", audio_buffer.getbuffer().nbytes)
        return audio_buffer

    except Exception:
        logger.exception("Errore sintesi ElevenLabs")
        # Restituisci buffer vuoto in caso di errore
        empty = BytesIO()
        empty.name = "error.mp3"
        return empty
