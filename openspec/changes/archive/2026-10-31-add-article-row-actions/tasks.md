# Tasks: add-article-row-actions

## 1. Action handlers (`language_study_anki/article_actions.py`)

- [x] 1.1 Implement `add_article(mw, parent)`: gate on
      `provisioning_ui.ensure_provisioned` (declining cancels, no dialog),
      build an empty `LSA-Article` note, open `dialogs.open("AddCards", mw)`
      with `set_note(note, current deck_id)`; verify: unit test asserts an
      empty note (all fields `""`) is handed to a stubbed AddCards and that
      a declined provisioning gate opens nothing.
- [x] 1.2 Implement `duplicate_article(mw, parent, note_id)`: build a fresh
      `LSA-Article` note whose `Content`/`Translation`/`Url`/`Cover` copy
      the source, `Title` = source + ` (Copy)`, progress fields empty, and
      open the Add dialog the same way; verify: unit test asserts copied
      fields, title suffix, empty progress fields, and that the source note
      object is not modified.
- [x] 1.3 Implement `edit_article(mw, parent, note_id)`: set
      `mw.reviewer.card` to the article's first card in a try/finally,
      `dialogs.open("EditCurrent", mw)`, restore the previous card value;
      verify: unit test with stubbed aqt asserts the dialog is opened while
      the seam holds the article's card and the previous value is restored
      afterwards, including when opening raises.
- [x] 1.4 Implement `delete_article(mw, parent, note_id)`: confirmation
      `QMessageBox` naming the article title; on confirm
      `col.remove_notes([note_id])`, on decline no collection call; verify:
      unit test asserts remove happens only after confirmation and never on
      decline.

## 2. Hub wiring and list UI

- [x] 2.1 Extend `hub.py` bridge dispatch with `lsa:add`, `lsa:edit:<id>`,
      `lsa:dup:<id>`, `lsa:del:<id>` routed to the handlers, refreshing the
      list via `show_list()` when an action's dialog closes / after a
      deletion; update the hub/list.html contract comment; verify:
      `python -m unittest tests.test_hub` passes with new dispatch cases
      (unknown id and non-article notes rejected like `show_practice`).
- [x] 2.2 Extend `web/list.html`: per-row "..." menu with Edit / Duplicate
      as New / Delete entries and a page-level Add button shown also in the
      empty state; entries emit the new pycmd commands; skill entries stay
      the only practice navigation; verify: static assertions in
      `tests/test_hub.py` cover the menu markup, the four commands, and the
      unchanged `lsa:open` contract.
- [x] 2.3 Verify the full contract comment block in `hub.py` and
      `list.html` lists all four new commands on both sides; verify:
      test asserts every command string appears in both files.

## 3. Self-test checks (Anki-integrated)

- [x] 3.1 Add `selftest_checks.py` check for edit: open edit from a row
      action, poll that the EditCurrent editor holds the article note
      (guards the `reviewer.card` seam), save, and verify note id and
      progress fields unchanged with the card still suspended.
- [x] 3.2 Add self-test checks for add and duplicate: drive the Add dialog
      to confirmation, then verify a new `LSA-Article` note exists with the
      expected fields (duplicate: ` (Copy)` title, copied fields, empty
      progress), card suspended, and the duplicate's source note unchanged.
- [x] 3.3 Add self-test check for delete: decline leaves the note; confirm
      removes the note and its cards.

## 4. End-to-end verification

- [x] 4.1 Run `python -m unittest discover tests` and verify all tests
      pass.
- [x] 4.2 Run `LSA_SELFTEST=1 tools/scratch-anki.sh --fresh` and verify
      `selftest-results.json` reports the new checks green (edit seam,
      add/duplicate creation + suspension, delete).
