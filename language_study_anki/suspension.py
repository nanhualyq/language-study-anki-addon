"""Keep article-note cards suspended (spec: article-storage → Articles never
enter the review queue; decision D2).

Enforcement points:
- when a note is added through Anki's Add dialog (creation)
- whenever the practice dialog opens an article (repairs cards regenerated
  unsuspended by template edits, which Anki rebuilds with default queues)
"""

from __future__ import annotations

import traceback

from .provisioning import ARTICLE_NOTE_TYPE

SUSPENDED_QUEUE = -1


def ensure_note_suspended(note) -> int:
    """Suspend every card of ``note``; returns how many cards changed."""
    col = note.col
    if col is None:
        return 0
    try:
        # Spike-verified: this API takes the note ID, not the Note object.
        card_ids = col.card_ids_of_note(note.id)
    except AttributeError:
        card_ids = [c.id for c in note.cards()]
    changed = 0
    for cid in card_ids:
        card = col.get_card(cid)
        if card.queue != SUSPENDED_QUEUE:
            card.queue = SUSPENDED_QUEUE
            card.flush()
            changed += 1
    return changed


def _is_article(note) -> bool:
    try:
        return note.note_type()["name"] == ARTICLE_NOTE_TYPE
    except Exception:
        return False


def _on_add_note(note) -> None:
    try:
        if _is_article(note):
            ensure_note_suspended(note)
    except Exception:
        print("language_study_anki: suspend-on-add failed:\n" + traceback.format_exc())


def register() -> None:
    from aqt import gui_hooks

    gui_hooks.add_cards_did_add_note.append(_on_add_note)
