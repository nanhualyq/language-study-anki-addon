"""Practice mode constants + thin adapter onto the Hub (spec: practice-hub).

The window and all practice-page logic live in ``hub.py`` (one Hub window,
list <-> practice pages). This module keeps the historical entry point
``open_dialog(parent, note_id, mode)`` — used by the self-test and any
direct callers — as a thin adapter that opens the Hub directly on the
given article's practice page.

D4 note: the practice rendering contract (templates, bridge commands) is
documented in hub.py; this module intentionally holds no window code.
"""

from __future__ import annotations

MODES = ("reading", "speaking", "listening", "writing")
MODE_LABELS = {
    "reading": "Practice: Reading",
    "speaking": "Practice: Speaking",
    "listening": "Practice: Listening",
    "writing": "Practice: Writing",
}


def open_dialog(parent, note_id: int, mode: str):
    """Open the Hub on ``note_id``'s practice page in ``mode``.

    Same signature and semantics as before the Hub existed (including
    ``parent=None`` from the self-test): returns the window so callers can
    probe ``web`` / ``selection`` / ``mode`` / ``close()`` as before.
    """
    assert mode in MODES, mode
    from .hub import open_hub

    return open_hub(parent, note_id=note_id, mode=mode)
