"""Article lifecycle actions (spec: article-management).

Every action is "open an Anki-native dialog with the known information
filled in" (design D1):

  add       -> AddCards holding a fresh, empty LSA-Article note
  duplicate -> AddCards holding a fresh note copied from the source
  edit      -> EditCurrent (the reviewer's `e` dialog) for the note
  delete    -> confirmation dialog, then col.remove_notes

Add and duplicate mirror the native "create copy" flow
(``Reviewer.on_create_copy``): ``AddCards.set_note`` clones the note into
the dialog's own state, so confirming creates a note and abandoning the
dialog creates nothing. Edit drives the EditCurrent dialog through the
``mw.reviewer.card`` seam (design D2) — the dialog reads its note from
there and saves in place on close. The four progress fields are never
written by these actions (design D6 keeps practice-extract's D8 "extract
is the only progress write path" true).

aqt is imported lazily so the module stays importable without Anki
(tests/ contract).
"""

from __future__ import annotations

from .progress import PROGRESS_FIELDS
from .provisioning import ARTICLE_NOTE_TYPE

CONFIRM_TITLE = "Language Study"
COPY_TITLE_SUFFIX = " (Copy)"
_COPY_FIELDS = ("Content", "Translation", "Url", "Cover")


# ------------------------------------------------------------- helpers


def _field(note, name: str) -> str:
    """Defensive article field read — empty string when absent (same
    belt-and-braces as extract._article_value)."""
    try:
        return note[name] or ""
    except KeyError:
        return ""


def _set_field(note, name: str, value: str) -> None:
    """Write one field only when the note type has it (adopted types may
    lack fields; extract.py uses the same guard)."""
    try:
        note[name] = value
    except KeyError:
        pass


def _article_note(col, note_id: int):
    """The article note with ``note_id``; rejects anything else the way
    ``HubWindow.show_practice`` does."""
    note = col.get_note(note_id)
    if note.note_type()["name"] != ARTICLE_NOTE_TYPE:
        raise ValueError("not an article note")
    return note


def fill_duplicate(note, source) -> None:
    """Fill a fresh ``note`` from ``source`` (spec: article-management ->
    Duplicate an article as new): ``Title`` gains the copy suffix,
    ``Content``/``Translation``/``Url``/``Cover`` are copied verbatim, and
    the four progress fields stay empty. ``source`` is only read."""
    _set_field(note, "Title", _field(source, "Title") + COPY_TITLE_SUFFIX)
    for name in _COPY_FIELDS:
        _set_field(note, name, _field(source, name))
    for name in PROGRESS_FIELDS.values():
        _set_field(note, name, "")


def current_deck_id(col):
    """The collection's current deck id across Anki API generations
    (design D3: mirror ``on_create_copy``). None when unavailable —
    AddCards then falls back to the deck last used with the note type."""
    for getter in (
        lambda: col.current_deck_id(),
        lambda: col.decks.selected(),
        lambda: col.decks.get_current_id(),
    ):
        try:
            return int(getter())
        except (AttributeError, TypeError):
            continue
    return None


def _open_add_dialog(mw, note):
    """Open Anki's Add dialog prefilled with ``note`` (extract.py
    pattern); returns the dialog."""
    from aqt import dialogs

    add_dlg = dialogs.open("AddCards", mw)
    deck_id = current_deck_id(mw.col)
    try:
        try:
            add_dlg.set_note(note, deck_id=deck_id)
        except TypeError:
            # Signature variance across Anki builds (see selftest_checks
            # _set_note_any): fall back to the positional form.
            add_dlg.set_note(note, deck_id)
    except Exception:
        # Never leave a half-initialized dialog behind.
        try:
            add_dlg.close()
        except Exception:
            pass
        raise
    return add_dlg


def _provision_article_type(mw, parent) -> dict | None:
    """Provisioning gate (design D6 / spec: article-management -> Actions
    require the article note type): returns the provision result, or None
    when the user declines — the action is cancelled, nothing created."""
    from .provisioning_ui import ensure_provisioned

    return ensure_provisioned(
        mw.col,
        parent,
        scope="article",
        context=(
            "Adding an article needs the following missing items before it "
            "can continue:"
        ),
    )


# ------------------------------------------------------------- actions


def add_article(mw, parent):
    """Global add (spec: article-management -> Add an article): the Add
    dialog on a fresh, empty ``LSA-Article`` note. Returns the dialog, or
    None when provisioning was declined."""
    prov = _provision_article_type(mw, parent)
    if prov is None:
        return None
    note = mw.col.new_note(prov["article_notetype"])
    return _open_add_dialog(mw, note)


def duplicate_article(mw, parent, note_id: int):
    """Duplicate as new (spec: article-management -> Duplicate an article
    as new). Returns the dialog, or None when provisioning was declined."""
    source = _article_note(mw.col, note_id)  # rejects like show_practice
    prov = _provision_article_type(mw, parent)
    if prov is None:
        return None
    note = mw.col.new_note(prov["article_notetype"])
    fill_duplicate(note, source)
    return _open_add_dialog(mw, note)


def edit_article(mw, parent, note_id: int):
    """In-place edit (spec: article-management -> Edit an article in
    place) via Anki's Edit Current dialog (design D2).

    The dialog takes its note from ``mw.reviewer.card.note()`` (verified
    against Anki 26.8.1: ``NewEditCurrent.__init__``/``reopen``), so the
    seam is set around the open call and restored afterwards — including
    when the open raises.
    """
    col = mw.col
    note = _article_note(col, note_id)  # rejects like show_practice
    card_ids = col.card_ids_of_note(note.id)
    if not card_ids:
        raise ValueError("article note has no card")
    card = col.get_card(card_ids[0])

    from aqt import dialogs

    reviewer = mw.reviewer
    saved_card = reviewer.card
    reviewer.card = card
    try:
        return dialogs.open("EditCurrent", mw)
    finally:
        reviewer.card = saved_card


def delete_article(mw, parent, note_id: int) -> bool:
    """Delete (spec: article-management -> Delete an article): confirm
    first — the dialog names the article — then remove the note and its
    cards. Returns True iff the note was removed."""
    col = mw.col
    note = _article_note(col, note_id)  # rejects like show_practice

    from aqt.qt import QMessageBox

    answer = QMessageBox.question(
        parent,
        CONFIRM_TITLE,
        'Are you sure you want to delete "{}"?\n'
        "This cannot be undone. All learning progress will also be "
        "deleted.".format(_field(note, "Title")),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,  # consent-first: Enter must not delete
    )
    if answer != QMessageBox.StandardButton.Yes:
        return False
    col.remove_notes([note_id])
    return True
