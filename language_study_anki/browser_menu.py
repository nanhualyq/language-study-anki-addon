"""Browser context-menu entry (spec: practice-dialog → Browser context-menu).

`build_menu_labels` is pure (testable); the hook glue resolves the selection
and opens the practice dialog for the first selected article.
"""

from __future__ import annotations

import traceback

from .practice_dialog import MODES, MODE_LABELS
from .progress import get_progress
from .provisioning import ARTICLE_NOTE_TYPE
from .storage import field_to_lines


def _progress_percent(note, skill: str) -> int:
    """Integer percent (0-100, half-up) of the note's Content covered by
    the skill's stored progress line. 0% for empty Content or no progress;
    100% when progress reaches/exceeds the line count."""
    try:
        total = len(field_to_lines(note["Content"]))
    except Exception:
        return 0
    if total <= 0:
        return 0
    line = get_progress(note, skill)
    if line <= 0:
        return 0
    if line >= total:
        return 100
    return int(line * 100.0 / total + 0.5)


def build_menu_labels(note_ids, col) -> list[tuple[str, str]] | None:
    """Return [(mode, "<label> (<pct>%)"), ...] when every selected note is
    an Article; None otherwise (menu items must not appear for non-article
    notes). Percentages describe the FIRST selected note — the note whose
    dialog opens when the item is chosen."""
    if not note_ids:
        return None
    first_note = None
    for index, nid in enumerate(note_ids):
        try:
            note = col.get_note(nid)
        except Exception:
            return None
        try:
            if note.note_type()["name"] != ARTICLE_NOTE_TYPE:
                return None
        except Exception:
            return None
        if index == 0:
            first_note = note
    return [
        (mode, f"{MODE_LABELS[mode]} ({_progress_percent(first_note, mode)}%)")
        for mode in MODES
    ]


def register() -> None:
    from aqt import gui_hooks

    gui_hooks.browser_will_show_context_menu.append(_on_context_menu)


def _on_context_menu(browser, menu) -> None:
    try:
        col = browser.col
        try:
            note_ids = browser.selected_notes()
        except AttributeError:
            note_ids = browser.selectedNotes()
        items = build_menu_labels(note_ids, col)
        if not items:
            return
        first_id = next(iter(note_ids))
        from aqt.qt import QAction
        from aqt import mw

        for mode, label in items:
            action = QAction(label, menu)
            action.triggered.connect(
                lambda checked=False, m=mode, nid=first_id: _open(browser, nid, m)
            )
            menu.addAction(action)
    except Exception:
        print("language_study_anki: context menu failed:\n" + traceback.format_exc())


def _open(browser, note_id: int, mode: str) -> None:
    from .practice_dialog import open_dialog

    open_dialog(browser, note_id, mode)
