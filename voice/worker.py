"""
LiveKit Agent Worker: collega la voice pipeline all'agente Agno Kira.

Gestisce:
- VAD (Voice Activity Detection) con Silero
- STT (Speech-to-Text) con Deepgram Nova-2 (italiano)
- TTS (Text-to-Speech) con ElevenLabs Turbo v2
- LLM backend tramite agente Kira (Agno)
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit.agents.llm import LLM, ChatContext, ChatChunk, Choice, ChoiceDelta
from livekit.agents.voice import AgentSession
from livekit.plugins import deepgram, elevenlabs, silero

from agent.config import settings
from agent.main import handle_request, init_agent, shutdown_agent

logger = logging.getLogger(__name__)

_initialized = False


class KiraLLM(LLM):
    """Custom LLM adapter che usa il pipeline Kira (routing + agente Agno)."""

    async def chat(self, *, chat_ctx: ChatContext, **kwargs) -> "KiraChatStream":
        # Estrai l'ultimo messaggio utente dal contesto
        last_message = ""
        for msg in reversed(chat_ctx.messages):
            if msg.role == "user" and msg.content:
                last_message = msg.content
                break

        return KiraChatStream(last_message)


class KiraChatStream:
    """Stream di risposta che wrappa il pipeline Kira."""

    def __init__(self, user_message: str):
        self._user_message = user_message
        self._task = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def __aiter__(self) -> AsyncIterator[ChatChunk]:
        try:
            response = await handle_request(self._user_message, user_id="alessandro")
        except Exception:
            logger.exception("Errore nel processing LLM")
            response = "Mi dispiace, ho avuto un problema. Puoi ripetere?"

        yield ChatChunk(
            choices=[Choice(delta=ChoiceDelta(content=response, role="assistant"))]
        )

    async def aclose(self):
        pass


async def entrypoint(ctx: JobContext):
    global _initialized

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
        llm=KiraLLM(),
    )

    await session.start(room=ctx.room)
    await session.say("Ciao Alessandro, sono Kira. Come posso aiutarti?")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )
