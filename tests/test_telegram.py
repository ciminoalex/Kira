"""
Test per i handler del bot Telegram.
"""

import pytest
from unittest.mock import patch, MagicMock


def test_parse_allowed_users():
    """Deve parsare correttamente la lista di user ID."""
    with patch("telegram_bot.bot.settings") as mock_settings:
        mock_settings.TELEGRAM_ALLOWED_USER_IDS = "123,456,789"
        mock_settings.TELEGRAM_BOT_TOKEN = "test"

        from telegram_bot.bot import _parse_allowed_users

        with patch("telegram_bot.bot.settings", mock_settings):
            users = _parse_allowed_users()
            assert users == {123, 456, 789}


def test_parse_allowed_users_single():
    """Deve funzionare con un singolo ID."""
    with patch("telegram_bot.bot.settings") as mock_settings:
        mock_settings.TELEGRAM_ALLOWED_USER_IDS = "123456789"
        mock_settings.TELEGRAM_BOT_TOKEN = "test"

        from telegram_bot.bot import _parse_allowed_users

        with patch("telegram_bot.bot.settings", mock_settings):
            users = _parse_allowed_users()
            assert users == {123456789}


def test_parse_allowed_users_empty():
    """Con stringa vuota deve restituire set vuoto."""
    with patch("telegram_bot.bot.settings") as mock_settings:
        mock_settings.TELEGRAM_ALLOWED_USER_IDS = ""
        mock_settings.TELEGRAM_BOT_TOKEN = "test"

        from telegram_bot.bot import _parse_allowed_users

        with patch("telegram_bot.bot.settings", mock_settings):
            users = _parse_allowed_users()
            assert users == set()


def test_calendar_utils_detect_conflicts():
    """Deve rilevare conflitti tra calendari diversi."""
    from datetime import datetime
    from agent.tools.calendar_utils import UnifiedEvent, detect_conflicts

    events = [
        UnifiedEvent(
            title="Meeting Gmail",
            start=datetime(2026, 4, 6, 10, 0),
            end=datetime(2026, 4, 6, 11, 0),
            source="gmail",
        ),
        UnifiedEvent(
            title="Call Outlook",
            start=datetime(2026, 4, 6, 10, 30),
            end=datetime(2026, 4, 6, 11, 30),
            source="outlook",
        ),
    ]

    result = detect_conflicts(events)
    assert result[0].is_conflict
    assert result[1].is_conflict
    assert result[0].conflict_with == "Call Outlook"


def test_calendar_utils_no_conflict_same_source():
    """Non deve rilevare conflitti tra eventi dello stesso calendario."""
    from datetime import datetime
    from agent.tools.calendar_utils import UnifiedEvent, detect_conflicts

    events = [
        UnifiedEvent(
            title="Meeting 1",
            start=datetime(2026, 4, 6, 10, 0),
            end=datetime(2026, 4, 6, 11, 0),
            source="gmail",
        ),
        UnifiedEvent(
            title="Meeting 2",
            start=datetime(2026, 4, 6, 10, 30),
            end=datetime(2026, 4, 6, 11, 30),
            source="gmail",
        ),
    ]

    result = detect_conflicts(events)
    assert not result[0].is_conflict
    assert not result[1].is_conflict


def test_calendar_format_events():
    """Deve formattare gli eventi correttamente."""
    from datetime import datetime
    from agent.tools.calendar_utils import UnifiedEvent, format_events_for_briefing

    events = [
        UnifiedEvent(
            title="Standup",
            start=datetime(2026, 4, 6, 9, 0),
            end=datetime(2026, 4, 6, 9, 30),
            source="outlook",
            location="Teams",
        ),
    ]

    result = format_events_for_briefing(events)
    assert "[O]" in result
    assert "Standup" in result
    assert "Teams" in result
