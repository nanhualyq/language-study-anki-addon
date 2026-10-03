"""Browser context-menu entry (spec: practice-dialog → Browser context-menu).

`build_menu_labels` is pure (testable); the hook glue resolves the selection
and opens the practice dialog for the first selected article.
"""

from __future__ import annotations

import traceback

from .practice_dialog import MODES, MODE_LABELS
from .provisioning import ARTICLE_NOTE_TYPE

# Spec wording: the menu offers exactly these four items.
MENU_ITEMS = [(mode, MODE_LABELS[mode]) for mode in MODES]


def build_menu_labels(note_ids, col) -> list[tuple[str, str]] | None:
    """Return [(mode, label), ...] when every selected note is an Article;
    None otherwise (menu items must not appear for non-article notes)."""
    if not note_ids:
        return None
    for nid in note_ids:
        try:
            note = col.get_note(nid)
        except Exception:
            return None
        try:
            if note.note_type()["name"] != ARTICLE_NOTE_TYPE:
                return None
        except Exception:
            return None
    return list(MENU_ITEMS)


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
