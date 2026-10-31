# Design: add-article-row-actions

See proposal.md for motivation. Specs: `specs/article-management`,
`specs/practice-hub`.

## Context

- The Hub list page (`web/list.html` + `hub.py`) renders rows whose only
  activatable entries are the four skill rings (`lsa:open:<id>:<mode>`).
  There is no article creation UI at all today.
- `extract.py` already proves the prefilled-Add-dialog pattern:
  `dialogs.open("AddCards", mw)` + `add_dlg.set_note(note, deck_id)`, with
  new notes suspended by the `add_cards_did_add_note` hook
  (`suspension.py`).
- Verified against the installed Anki 26.8.1 (`app_packages` bytecode and
  `editor.js`):
  - `NewAddCards.set_note(note, deck_id)` clones the note into the dialog's
    own state — the caller's note object never receives an id, so saving
    always CREATES a note. This is exactly what the native "create copy"
    (`Reviewer.on_create_copy`, `Ctrl+Alt+E`) relies on: it passes the
    current, existing note to `set_note` and the result is a new note.
  - `NewEditCurrent.__init__`/`reopen` both call
    `editor.set_note(mw.reviewer.card.note())` — the dialog has no note
    parameter — and save in place on close
    (`closeEvent -> editor.call_after_note_saved`). `Reviewer.card` is a
    plain instance attribute (`Reviewer.__init__: self.card = None`), so it
    can be temporarily reassigned as a seam.
- Reference app (`../my_english_ankier_flutter`): row menu = Edit / Save As
  / Reset Progress / Delete; add and save-as create the record first and
  then open the edit page; the edit form has Title / Url / Content /
  Translation only. Delete and reset confirm first.

## Goals / Non-Goals

**Goals:**

- Every action is "open an Anki-native dialog with the known information
  already filled in" — no custom edit form anywhere.
- Edit writes back in place (note id, progress fields, suspended card
  preserved); add and duplicate create notes only when the user confirms
  the Add dialog.
- Keep the progress invariant: the four progress fields are never written
  by these actions (extract remains the only progress write path).
- Extend the existing pycmd bridge contract rather than introducing a new
  communication mechanism.

**Non-Goals:**

- Reset Progress (present in the reference app; not requested).
- A dedicated Cover editor; `Cover` is copied on duplicate and otherwise
  left to Anki's own note editing.
- Any change to the extract or practice flows, TTS, or note-type schemas.
- Article deck management (deck stays arbitrary, per article-storage).

## Decisions

**D1 — All four actions drive native dialogs (AddCards / EditCurrent).**
The user's target behavior ("just open the edit dialog, prefilled") is
natively implemented by Anki for three of the four actions. Alternatives
considered: a custom QDialog form (rejected: new UI surface to build and
test, and edit-in-place would be hand-rolled anyway) and editing via the
Browser (rejected: heavyweight window for a single-note edit).

**D2 — Edit = EditCurrent driven through the `mw.reviewer.card` seam.**
Set `mw.reviewer.card` to the article's first card, open via
`dialogs.open("EditCurrent", mw)`, restore the previous value in a
`try/finally`. Both the fresh-open and the singleton-reopen code path read
`reviewer.card`, so the seam covers repeated opens. Alternative — passing
the note via `dlg.editor.set_note(...)` after open — is rejected because
`NewEditCurrent.__init__` dereferences `mw.reviewer.card` first (crash when
no review is in progress) and races the editor's async load.

**D3 — Add and Duplicate share the AddCards path; Duplicate passes a fresh
note with copied fields.** For duplicate, build `col.new_note(ARTICLE)`
with `Content`/`Translation`/`Url`/`Cover` copied from the source, `Title`
suffixed ` (Copy)`, and the four progress fields left empty, then hand it
to `set_note`. Passing a fresh (id-less) note keeps the prefill entirely
under our control and guarantees empty progress fields regardless of
whether the dialog resolves its prefill from the passed object or from
`originalNoteId`. Deck = the collection's current deck, mirroring
`on_create_copy` (article deck is arbitrary). Alternatives: passing the
existing source note to `set_note` like `on_create_copy` (rejected: the
copy would carry the source's progress values) and create-first-then-edit
(reference behavior; rejected in favor of "nothing exists until Add").

**D4 — Delete = confirmation dialog, then `col.remove_notes([nid])`,
then re-render.** Declining changes nothing. The native `Ctrl+Delete`
deletes without confirmation; the user explicitly chose to confirm first.

**D5 — UI and bridge: per-row "..." popup menu (edit / duplicate / delete)
plus a page-level Add button; new commands `lsa:edit:<id>`, `lsa:dup:<id>`,
`lsa:del:<id>`, `lsa:add`.** Same contract style as `lsa:open` (documented
in the hub/list.html header comments). Actions run in the Hub window; the
list re-renders via the existing `show_list()` (fresh collection read) when
an action's dialog closes or a deletion completes.

**D6 — Provisioning gate reuses `provisioning_ui.ensure_provisioned`.**
Add and duplicate need `LSA-Article`; declining the provisioning
confirmation cancels the action (same contract as extract-time
provisioning). Delete and edit need no provisioning (the note exists).

## Risks / Trade-offs

- [EditCurrent is a registered singleton; opening edit for note B while
  note A is being edited reopens the dialog on B] → save-or-close any open
  EditCurrent before switching (its close path already saves via
  `call_after_note_saved`); document behavior as Anki's own.
- [`mw.reviewer.card` is a seam, not public API; a future Anki may change
  `NewEditCurrent`'s note source] → wrap in try/finally restore; a
  self-test check (open edit from the list, verify the dialog holds the
  article note) fails loudly if the seam breaks.
- [Both native editors show the four progress fields; a user can hand-edit
  them] → accepted: identical to editing the note in Anki's Browser today.
  The system itself never writes them, keeping the extract-only invariant.
- [The Add dialog stays open for consecutive adds] → the list refreshes
  when the dialog closes, so all accumulated additions appear at once;
  percentages are recomputed on that render.
- [Duplicate title suffix can collide across copies] → harmless: ` (Copy)`
  is only a convenience label; notes remain distinguished by id.

## Migration Plan

Additive change; no data migration. Rollback = remove the menu/button and
bridge commands; existing article notes are unaffected.

## Open Questions

None.
