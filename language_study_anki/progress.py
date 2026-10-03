"""Per-skill progress fields on article notes.

Spec: article-storage → Per-skill progress fields.
Decision D8 (revised): progress is written **only by the extract flow** —
scrolling and dialog close never write. Values are 1-based last *extracted*
line numbers; ``0`` means no progress; writes are monotonic.
"""

from __future__ import annotations

PROGRESS_FIELDS = {
    "listening": "ProgListening",
    "speaking": "ProgSpeaking",
    "reading": "ProgReading",
    "writing": "ProgWriting",
}


def progress_field(skill: str) -> str:
    """Field name for a skill; raises KeyError for unknown skills."""
    return PROGRESS_FIELDS[skill]


def get_progress(note, skill: str) -> int:
    """Read a skill's progress line (0 when unset/invalid)."""
    try:
        raw = str(note[PROGRESS_FIELDS[skill]]).strip()
    except (KeyError, TypeError):
        return 0
    try:
        value = int(raw)
    except ValueError:
        return 0
    return max(0, value)


def set_progress_at_least(note, skill: str, line: int, *, flush: bool = True) -> bool:
    """Monotonically advance a skill's progress to at least ``line``.

    The only write path for progress fields. Returns True iff the field
    changed (and flushes the note when ``flush`` is true).
    """
    if line <= 0:
        return False
    if line <= get_progress(note, skill):
        return False
    note[PROGRESS_FIELDS[skill]] = str(int(line))
    if flush:
        note.flush()
    return True
