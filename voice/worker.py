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
import uuid

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit.agents.llm import LLM, LLMStream, ChatContext, ChatChunk, ChoiceDelta
from livekit.agents.llm.llm import APIConnectOptions, Tool
from livekit.agents.voice import AgentSession
from livekit.plugins import deepgram, elevenlabs, silero

from agent.config import settings
from agent.main import handle_request, init_agent, shutdown_agent

logger = logging.getLogger(__name__)

_initialized = False


class KiraLLMStream(LLMStream):
    """Stream di risposta che wrappa il pipeline Kira."""

    def __init__(self, *, llm: LLM, chat_ctx: ChatContext, conn_options: APIConnectOptions):
        super().__init__(llm, chat_ctx=chat_ctx, tools=[], conn_options=conn_options)
        self._user_message = ""
        for msg in reversed(chat_ctx.messages):
            if msg.role == "user" and msg.content:
                self._user_message = msg.content if isinstance(msg.content, str) else str(msg.content)
                break

    async def _run(self) -> None:
        try:
            response = await handle_request(self._user_message, user_id="alessandro")
        except Exception:
            logger.exception("Errore nel processing LLM")
            response = "Mi dispiace, ho avuto un problema. Puoi ripetere?"

        chunk = ChatChunk(
            id=str(uuid.uuid4()),
            delta=ChoiceDelta(content=response, role="assistant"),
        )
        self._event_ch.send_nowait(chunk)


class KiraLLM(LLM):
    """Custom LLM adapter che usa il pipeline Kira (routing + agente Agno)."""

    def chat(
        self,
        *,
        chat_ctx: ChatContext,
        tools: list[Tool] | None = None,
        conn_options: APIConnectOptions = APIConnectOptions(),
        **kwargs,
    ) -> KiraLLMStream:
        return KiraLLMStream(llm=self, chat_ctx=chat_ctx, conn_options=conn_options)


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
