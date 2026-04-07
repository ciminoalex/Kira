"""
Definizione dell'agente Kira con Agno framework + MCP tools.
"""

from __future__ import annotations

import logging
from pathlib import Path

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.postgres import PostgresStorage
from agno.tools.mcp import MCPTools

from agent.config import settings
from agent.tools.reminder import (
    create_reminder,
    list_reminders,
    delete_reminder,
    get_due_reminders,
)
from agent.tools.notes import save_note, search_notes, list_notes, delete_note
from agent.tools.claude_code import execute_claude_code, execute_claude_code_with_session

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = Path(__file__).parent / "prompts" / "system_prompt.md"


def _build_mcp_tools() -> list[MCPTools]:
    """Costruisce la lista di MCP tool servers."""
    mcp_tools: list[MCPTools] = []

    # Gmail MCP (mail)
    if settings.GOOGLE_CLIENT_ID:
        mcp_tools.append(
            MCPTools(
                command="npx",
                args=["-y", "@anthropic/gmail-mcp-server"],
                env={
                    "GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
                    "GOOGLE_CLIENT_SECRET": settings.GOOGLE_CLIENT_SECRET,
                    "GOOGLE_REFRESH_TOKEN": settings.GOOGLE_REFRESH_TOKEN,
                },
            )
        )

    # Google Calendar MCP
    if settings.GOOGLE_CLIENT_ID:
        mcp_tools.append(
            MCPTools(
                command="npx",
                args=["-y", "@anthropic/google-calendar-mcp-server"],
                env={
                    "GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
                    "GOOGLE_CLIENT_SECRET": settings.GOOGLE_CLIENT_SECRET,
                    "GOOGLE_REFRESH_TOKEN": settings.GOOGLE_REFRESH_TOKEN,
                },
            )
        )

    # Supermemory MCP (memory, recall, context)
    if settings.SUPERMEMORY_API_KEY:
        mcp_tools.append(
            MCPTools(
                url="https://mcp.supermemory.ai/mcp",
                transport="streamable-http",
                headers={"Authorization": f"Bearer {settings.SUPERMEMORY_API_KEY}"},
            )
        )

    # Microsoft 365 MCP (Outlook mail + calendar + contacts)
    if settings.MS365_CLIENT_ID:
        mcp_tools.append(
            MCPTools(
                command="npx",
                args=[
                    "-y", "@softeria/ms-365-mcp-server",
                    "--preset", "email,calendar,contacts",
                ],
                env={
                    "MS365_MCP_CLIENT_ID": settings.MS365_CLIENT_ID,
                    "MS365_MCP_TENANT_ID": settings.MS365_TENANT_ID,
                },
            )
        )

    # Web Search (Tavily)
    if settings.TAVILY_API_KEY:
        mcp_tools.append(
            MCPTools(
                command="npx",
                args=["-y", "@tavily/mcp-server"],
                env={"TAVILY_API_KEY": settings.TAVILY_API_KEY},
            )
        )

    # Filesystem PC (via Tailscale, opzionale)
    if settings.PC_TAILSCALE_IP:
        import httpx as _httpx

        pc_url = f"http://{settings.PC_TAILSCALE_IP}:{settings.PC_FILESYSTEM_PORT}"
        try:
            r = _httpx.get(f"{pc_url}/health", timeout=2)
            if r.status_code == 200:
                mcp_tools.append(
                    MCPTools(url=pc_url, transport="streamable-http")
                )
                logger.info("PC filesystem connesso via Tailscale")
        except Exception:
            logger.info("PC fisso non raggiungibile, proseguo senza filesystem")

    return mcp_tools


def _build_custom_tools() -> list:
    """Costruisce la lista di tool custom (funzioni Python)."""
    return [
        create_reminder,
        list_reminders,
        delete_reminder,
        get_due_reminders,
        save_note,
        search_notes,
        list_notes,
        delete_note,
        execute_claude_code,
        execute_claude_code_with_session,
    ]


def create_kira_agent(mcp_tools: list[MCPTools] | None = None) -> Agent:
    """
    Crea e configura l'agente Kira.

    Args:
        mcp_tools: Lista di MCPTools già connessi. Se None, vengono creati
                   (ma dovranno essere connessi dal chiamante).
    """
    if mcp_tools is None:
        mcp_tools = _build_mcp_tools()

    system_prompt = SYSTEM_PROMPT.read_text(encoding="utf-8")

    storage = PostgresStorage(
        table_name="kira_sessions",
        db_url=settings.db_url,
    )

    agent = Agent(
        name="Kira",
        model=Claude(id="claude-sonnet-4-6"),
        description="Kira — Assistente personale di Alessandro Cimino",
        instructions=system_prompt,
        tools=[*mcp_tools, *_build_custom_tools()],
        storage=storage,
        add_history_to_context=True,
        num_history_runs=10,
        markdown=True,
        reasoning=True,
    )

    return agent


async def start_agent_with_mcp() -> tuple[Agent, list[MCPTools]]:
    """
    Crea l'agente e connette tutti i server MCP.
    Il chiamante è responsabile di chiudere le connessioni MCP.

    Returns:
        Tupla (agent, mcp_tools_list) per gestione lifecycle.
    """
    mcp_tools = _build_mcp_tools()

    for tool_server in mcp_tools:
        try:
            await tool_server.connect()
            logger.info("MCP connesso: %s", tool_server)
        except Exception:
            logger.exception("Errore connessione MCP: %s", tool_server)

    agent = create_kira_agent(mcp_tools=mcp_tools)
    return agent, mcp_tools


async def stop_mcp_tools(mcp_tools: list[MCPTools]) -> None:
    """Chiude tutte le connessioni MCP."""
    for tool_server in mcp_tools:
        try:
            await tool_server.close()
        except Exception:
            logger.exception("Errore chiusura MCP: %s", tool_server)
