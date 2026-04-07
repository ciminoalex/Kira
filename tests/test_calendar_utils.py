"""
Test per le utilità calendario unificate (Phase 2).
"""

from datetime import datetime

from agent.tools.calendar_utils import (
    UnifiedEvent,
    detect_conflicts,
    find_free_slots,
    format_free_slots,
    format_events_for_briefing,
)


def _make_event(title, start_h, start_m, end_h, end_m, source="gmail"):
    return UnifiedEvent(
        title=title,
        start=datetime(2026, 4, 7, start_h, start_m),
        end=datetime(2026, 4, 7, end_h, end_m),
        source=source,
    )


def test_find_free_slots_basic():
    """Deve trovare slot liberi tra gli eventi."""
    events = [
        _make_event("Meeting", 10, 0, 11, 0),
        _make_event("Call", 14, 0, 15, 0),
    ]
    day_start = datetime(2026, 4, 7, 9, 0)
    day_end = datetime(2026, 4, 7, 18, 0)

    slots = find_free_slots(events, day_start, day_end)

    assert len(slots) == 3  # 9-10, 11-14, 15-18
    assert slots[0] == (day_start, datetime(2026, 4, 7, 10, 0))
    assert slots[1] == (datetime(2026, 4, 7, 11, 0), datetime(2026, 4, 7, 14, 0))
    assert slots[2] == (datetime(2026, 4, 7, 15, 0), day_end)


def test_find_free_slots_no_events():
    """Senza eventi, tutta la giornata è libera."""
    day_start = datetime(2026, 4, 7, 9, 0)
    day_end = datetime(2026, 4, 7, 18, 0)

    slots = find_free_slots([], day_start, day_end)

    assert len(slots) == 1
    assert slots[0] == (day_start, day_end)


def test_find_free_slots_min_duration():
    """Non deve restituire slot più corti della durata minima."""
    events = [
        _make_event("A", 9, 0, 9, 50),
        _make_event("B", 10, 0, 11, 0),
    ]
    day_start = datetime(2026, 4, 7, 9, 0)
    day_end = datetime(2026, 4, 7, 11, 30)

    # Slot di 10 min (9:50-10:00) non deve apparire con min 30
    slots = find_free_slots(events, day_start, day_end, min_duration_minutes=30)
    assert len(slots) == 1  # Solo 11:00-11:30


def test_format_free_slots():
    """Deve formattare gli slot con durata."""
    slots = [
        (datetime(2026, 4, 7, 9, 0), datetime(2026, 4, 7, 10, 0)),
        (datetime(2026, 4, 7, 15, 0), datetime(2026, 4, 7, 18, 0)),
    ]
    result = format_free_slots(slots)
    assert "09:00-10:00" in result
    assert "60 min" in result
    assert "180 min" in result


def test_cross_calendar_conflict():
    """Deve rilevare conflitti tra Gmail e Outlook."""
    events = [
        _make_event("Personal", 10, 0, 11, 0, "gmail"),
        _make_event("Work call", 10, 30, 11, 30, "outlook"),
    ]
    result = detect_conflicts(events)
    assert result[0].is_conflict
    assert result[1].is_conflict


def test_no_conflict_sequential():
    """Eventi sequenziali non devono essere in conflitto."""
    events = [
        _make_event("A", 10, 0, 11, 0, "gmail"),
        _make_event("B", 11, 0, 12, 0, "outlook"),
    ]
    result = detect_conflicts(events)
    assert not result[0].is_conflict
    assert not result[1].is_conflict


def test_briefing_format_with_outlook():
    """Il briefing deve mostrare tag [O] per Outlook."""
    events = [
        _make_event("Standup", 9, 0, 9, 30, "outlook"),
        _make_event("Dentista", 14, 0, 15, 0, "gmail"),
    ]
    result = format_events_for_briefing(events)
    assert "[O]" in result
    assert "[G]" in result
    assert "Standup" in result
    assert "Dentista" in result
