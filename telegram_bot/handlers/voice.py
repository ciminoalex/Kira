"""
Handler per messaggi vocali: STT → Agente → TTS → risposta audio.
"""

from __future__ import annotations

import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, BufferedInputFile

from agent.main import handle_request
from telegram_bot.services.stt import transcribe_voice
from telegram_bot.services.tts import synthesize_speech

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.voice)
async def handle_voice(message: Message, bot: Bot) -> None:
    """Gestione messaggi vocali: STT → Agente → TTS → risposta audio."""
    await message.chat.do("typing")

    # 1. Download audio da Telegram
    file = await bot.get_file(message.voice.file_id)
    audio_io = await bot.download_file(file.file_path)
    audio_bytes = audio_io.read()

    # 2. Trascrivi con Deepgram
    transcript = await transcribe_voice(audio_bytes)
    if not transcript:
        await message.answer("Non sono riuscita a capire il messaggio vocale.")
        return

    logger.info("Vocale trascritto: %s", transcript[:80])

    # 3. Invia all'agente
    response = await handle_request(transcript)

    # 4. Rispondi con testo
    await message.answer(response, parse_mode="Markdown")

    # 5. Sintetizza e invia risposta vocale
    try:
        audio_response = await synthesize_speech(response)
        audio_data = audio_response.read()
        if audio_data:
            voice_file = BufferedInputFile(audio_data, filename="response.ogg")
            await message.answer_voice(voice=voice_file)
    except Exception:
        logger.debug("Errore sintesi vocale", exc_info=True)
