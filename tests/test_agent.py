"""
Test per la creazione e configurazione dell'agente Kira.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


def test_system_prompt_exists():
    """Il file system prompt deve esistere."""
    prompt_path = Path(__file__).parent.parent / "agent" / "prompts" / "system_prompt.md"
    assert prompt_path.exists()
    content = prompt_path.read_text(encoding="utf-8")
    assert "Kira" in content
    assert "Alessandro" in content


def test_config_defaults():
    """Le impostazioni di default devono essere valide."""
    from agent.config import Settings

    with patch.dict("os.environ", {}, clear=False):
        s = Settings(
            _env_file=None,
            POSTGRES_PASSWORD="test",
            TELEGRAM_BOT_TOKEN="test",
        )
        assert s.POSTGRES_HOST == "localhost"
        assert s.POSTGRES_PORT == 5432
        assert s.BRIEFING_TIME == "07:30"
        assert s.SUPERMEMORY_CONTAINER_TAG == "kira_alessandro"
        assert s.DEFAULT_MODEL_TIER == "advanced"


def test_db_url_format():
    """L'URL del database deve avere il formato corretto."""
    from agent.config import Settings

    s = Settings(
        _env_file=None,
        POSTGRES_USER="testuser",
        POSTGRES_PASSWORD="testpass",
        POSTGRES_HOST="localhost",
        POSTGRES_PORT=5432,
        POSTGRES_DB="testdb",
    )
    assert "testuser" in s.db_url
    assert "testpass" in s.db_url
    assert "testdb" in s.db_url


def test_build_custom_tools():
    """I tool custom devono essere costruiti correttamente."""
    from agent.kira_agent import _build_custom_tools

    tools = _build_custom_tools()
    assert len(tools) == 10  # 4 reminder + 4 notes + 2 claude_code
    # Verifica che siano tutti callable
    for t in tools:
        assert callable(t)


def test_build_mcp_tools_empty_config():
    """Con config vuota, nessun MCP tool viene creato."""
    from agent.kira_agent import _build_mcp_tools

    with patch("agent.kira_agent.settings") as mock_settings:
        mock_settings.GOOGLE_CLIENT_ID = ""
        mock_settings.SUPERMEMORY_API_KEY = ""
        mock_settings.TAVILY_API_KEY = ""
        tools = _build_mcp_tools()
        assert len(tools) == 0
