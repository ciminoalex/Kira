"""
LiveKit Agent Worker: collega la voice pipeline all'agente Agno Kira.

Gestisce:
- VAD (Voice Activity Detection) con Silero
- STT (Speech-to-Text) con Deepgram Nova-2 (italiano)
- TTS (Text-to-Speech) con ElevenLabs Turbo v2
- LLM backend tramite agente Kira (Agno)
"""

from __future__ import annotations

import logging

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit.agents.voice import AgentSession
from livekit.agents.llm import LLMNode
from livekit.plugins import deepgram, elevenlabs, silero

from agent.config import settings
from agent.main import handle_request, init_agent, shutdown_agent

logger = logging.getLogger(__name__)

# Flag per inizializzazione one-time
_initialized = False


class KiraLLMNode(LLMNode):
    """Custom LLM node che usa il pipeline Kira (routing + agente Agno)."""

    async def run(self, text: str) -> str:
        try:
            return await handle_request(text, user_id="alessandro")
        except Exception:
            logger.exception("Errore nel processing LLM")
            return "Mi dispiace, ho avuto un problema. Puoi ripetere?"


async def entrypoint(ctx: JobContext):
    global _initialized

    # Inizializza l'agente una sola volta
    if not _initialized:
        await init_agent()
        _initialized = True

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    session = AgentSession(
        stt=deepgram.STT(
            model="nova-2",
            language="it",
        ),
        tts=elevenlabs.TTS(
            voice_id=settings.ELEVENLABS_VOICE_ID,
            model="eleven_turbo_v2",
        ),
        vad=silero.VAD.load(
            min_silence_duration=0.5,
            speech_threshold=0.5,
        ),
        llm=KiraLLMNode(),
    )

    await session.start(room=ctx.room)

    # Messaggio di benvenuto
    await session.say("Ciao Alessandro, sono Kira. Come posso aiutarti?")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )
