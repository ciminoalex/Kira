"""
Utility per unificare i calendari Gmail e Outlook.
Usate dall'agente per:
- Generare una vista unificata degli appuntamenti
- Rilevare conflitti tra i due calendari
- Identificare slot liberi
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class UnifiedEvent:
    title: str
    start: datetime
    end: datetime
    source: str  # "gmail" | "outlook"
    location: str | None = None
    attendees: list[str] = field(default_factory=list)
    is_conflict: bool = False
    conflict_with: str | None = None


def detect_conflicts(events: list[UnifiedEvent]) -> list[UnifiedEvent]:
    """Rileva conflitti temporali tra eventi di calendari diversi."""
    sorted_events = sorted(events, key=lambda e: e.start)

    for i, event_a in enumerate(sorted_events):
        for event_b in sorted_events[i + 1 :]:
            if event_b.start >= event_a.end:
                break
            # Conflitto solo tra calendari diversi
            if event_a.source != event_b.source:
                event_a.is_conflict = True
                event_a.conflict_with = event_b.title
                event_b.is_conflict = True
                event_b.conflict_with = event_a.title

    return sorted_events


def format_events_for_briefing(events: list[UnifiedEvent]) -> str:
    """Formatta gli eventi per il briefing testuale."""
    if not events:
        return "Nessun appuntamento oggi."

    sorted_events = detect_conflicts(events)
    lines = []

    for event in sorted_events:
        time_str = (
            f"{event.start.strftime('%H:%M')}-{event.end.strftime('%H:%M')}"
        )
        source_tag = "G" if event.source == "gmail" else "O"
        location_str = f" @ {event.location}" if event.location else ""
        conflict_str = f" ⚠️ CONFLITTO con: {event.conflict_with}" if event.is_conflict else ""

        lines.append(
            f"[{source_tag}] {time_str} — {event.title}{location_str}{conflict_str}"
        )

    return "\n".join(lines)
