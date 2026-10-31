# Proposal: add-article-row-actions

## Why

The Hub's article list renders rows but offers no way to act on them: an
article can only be created by hand through Anki's Add dialog, and once in
the list it can neither be edited nor removed. The reference app's row menu
(edit / save-as / delete) and its global add action have no counterpart in
the addon, so the article library cannot be managed from the list at all.

## What Changes

- Each article row gains an action menu with three entries: **Edit**,
  **Duplicate as New** (复制新建), and **Delete**.
- The article list page gains a global **Add** entry.
- **Edit** opens Anki's native Edit Current dialog (the reviewer's `e`
  dialog) for the row's note; saving is in place — note id, the four
  progress fields, and the suspended card state are preserved.
- **Duplicate as New** opens Anki's native Add dialog (the same flow behind
  the reviewer's `Ctrl+Alt+E` "create copy") prefilled from the source
  article: content fields copied, the four progress fields empty, title
  suffixed ` (Copy)`. Nothing is created until the user presses Add.
- **Add** opens the same Add dialog with a fresh, empty `LSA-Article` note
  (the main-window `a` semantics). Nothing is created until the user
  presses Add.
- **Delete** shows a confirmation dialog first, then removes the note and
  its cards; the list re-renders afterwards.
- All four actions go through Anki's own dialogs — no custom edit form is
  introduced.

## Capabilities

### New Capabilities

- `article-management`: lifecycle actions on article notes — add, edit,
  duplicate-as-new, delete — including which native dialog each action
  opens, what is prefilled, and what a save preserves or resets.

### Modified Capabilities

- `practice-hub`: the Article list page requirement gains per-row action
  entries, the global add entry, and the bridge commands that trigger the
  four actions.

## Impact

- `language_study_anki/web/list.html` — row action menu and global add
  entry markup/JS; new bridge commands added to the template contract.
- `language_study_anki/hub.py` — dispatch the new bridge commands to the
  action handlers; extend the list payload if the row menu needs data.
- New `language_study_anki/article_actions.py` — action handlers driving
  `aqt.dialogs` AddCards (`set_note`) and EditCurrent (via the
  `mw.reviewer.card` seam), the delete confirmation, and note removal.
- `language_study_anki/suspension.py` — reused unchanged (notes created
  through the Add dialog are suspended by the existing hook).
- `language_study_anki/provisioning.py` / `provisioning_ui.py` — add
  requires the `LSA-Article` note type to exist; reuse the existing
  provisioning gate.
- Tests: `tests/` unit coverage for payload/dispatch helpers and
  `language_study_anki/selftest_checks.py` checks for the four dialog flows.
