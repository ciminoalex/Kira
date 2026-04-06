"""
Tool per eseguire Claude Code CLI in modalità headless (-p).
Sfrutta la subscription MAX per task di coding senza costi API.

Prerequisiti:
- Claude Code CLI installato sulla VPS
- Autenticazione configurata (claude auth login)
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from agno.tools import tool

from agent.config import settings

logger = logging.getLogger(__name__)

# Tool permessi in modalità headless
ALLOWED_TOOLS = [
    "Read",
    "Edit",
    "Write",
    "Glob",
    "Grep",
    "Bash(git *)",
    "Bash(python *)",
    "Bash(npm *)",
    "Bash(dotnet *)",
    "Bash(ls *)",
]


@tool(name="claude_code", description=(
    "Esegue un task di coding usando Claude Code CLI in modalità headless. "
    "Usa questo tool per: scrivere codice, debug, refactoring, analisi codebase, "
    "esecuzione comandi git. Parametri: prompt (str), "
    "working_directory (str, opzionale)."
))
async def execute_claude_code(
    prompt: str,
    working_directory: str | None = None,
) -> str:
    """Esegue Claude Code CLI in modalità headless (-p)."""
    workdir = Path(working_directory) if working_directory else Path(settings.CLAUDE_CODE_WORKDIR)

    cmd = [
        "claude",
        "-p", prompt,
        "--output-format", "json",
        "--allowedTools", ",".join(ALLOWED_TOOLS),
        "--max-budget-usd", str(settings.CLAUDE_CODE_MAX_BUDGET),
    ]

    logger.info("Executing Claude Code: %s", prompt[:100])

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(workdir),
        )

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=settings.CLAUDE_CODE_TIMEOUT,
        )

        if proc.returncode != 0:
            error_msg = stderr.decode().strip()
            logger.error("Claude Code error: %s", error_msg)
            return f"Errore Claude Code: {error_msg}"

        result = json.loads(stdout.decode())
        response_text = result.get("result", "Nessun output.")
        cost = result.get("total_cost_usd", 0)
        duration = result.get("duration_ms", 0)

        logger.info(
            "Claude Code completato in %dms (costo: $%.4f)",
            duration, cost,
        )
        return response_text

    except asyncio.TimeoutError:
        logger.error("Claude Code timeout dopo %ds", settings.CLAUDE_CODE_TIMEOUT)
        proc.kill()
        return f"Timeout: Claude Code non ha completato entro {settings.CLAUDE_CODE_TIMEOUT}s."
    except FileNotFoundError:
        return "Errore: Claude Code CLI non installato. Installa con: curl -fsSL https://claude.ai/install.sh | sh"
    except Exception as e:
        logger.exception("Claude Code exception")
        return f"Errore imprevisto: {e}"


@tool(name="claude_code_session", description=(
    "Esegue un task di coding con Claude Code in una sessione continuabile. "
    "Può continuare una sessione precedente per task multi-step. "
    "Parametri: prompt (str), project_path (str), "
    "session_id (str, opzionale per continuare una sessione)."
))
async def execute_claude_code_with_session(
    prompt: str,
    project_path: str,
    session_id: str | None = None,
) -> str:
    """Esegue Claude Code con supporto sessioni continuabili."""
    cmd = [
        "claude",
        "-p", prompt,
        "--output-format", "json",
        "--allowedTools", ",".join(ALLOWED_TOOLS),
    ]

    if session_id:
        cmd.extend(["--resume", session_id])

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=project_path,
        )

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=settings.CLAUDE_CODE_TIMEOUT,
        )

        if proc.returncode != 0:
            return f"Errore: {stderr.decode().strip()}"

        result = json.loads(stdout.decode())
        sid = result.get("session_id", "")
        response = result.get("result", "Nessun output.")

        return f"{response}\n\n[Session ID: {sid}]"

    except asyncio.TimeoutError:
        proc.kill()
        return "Timeout nella sessione Claude Code."
    except Exception as e:
        return f"Errore: {e}"
