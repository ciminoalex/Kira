"""
Configurazione della voice pipeline LiveKit.
Contiene factory functions per i componenti STT, TTS, VAD.
"""

from __future__ import annotations

from livekit.plugins import deepgram, elevenlabs, silero

from agent.config import settings


def create_stt(language: str = "it") -> deepgram.STT:
    """Crea il componente Speech-to-Text (Deepgram Nova-2)."""
    return deepgram.STT(
        model="nova-2",
        language=language,
        smart_format=True,
        punctuate=True,
    )


def create_tts() -> elevenlabs.TTS:
    """Crea il componente Text-to-Speech (ElevenLabs Turbo v2)."""
    return elevenlabs.TTS(
        voice_id=settings.ELEVENLABS_VOICE_ID,
        model="eleven_turbo_v2",
        output_format="pcm_24000",
    )


def create_vad() -> silero.VAD:
    """Crea il componente Voice Activity Detection (Silero)."""
    return silero.VAD.load(
        min_silence_duration=0.5,
        speech_threshold=0.5,
    )
