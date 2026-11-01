## Why

Every interaction in the Hub today requires the mouse: picking a skill entry in the list, opening row menus, revealing per-line hidden text, playing a line, and above all drag-selecting a phrase before pressing `a` to extract. The study loop is line-repetitive, so mouse travel dominates the time per article. A vim-style keyboard layer removes the mouse from the loop entirely.

## What Changes

- **Practice page keyboard layer** — a line cursor (`j`/`k`, `gg`/`G`) plus an in-line character cursor (`h`/`l`, word motions `w`/`b`/`e`); `v` charwise / `V` linewise visual selection that feeds the existing selection→extract pipeline; `Enter` toggles per-line reveal; `p`/`Space` TTS-plays the current line; `q` returns to the list; `Esc` cancels the selection; `?` shows a keymap overlay. The existing bare-`a` extract shortcut is unchanged and works with keyboard-made or mouse-made selections alike.
- **List page keyboard layer** — a row cursor (`j`/`k`) with a skill-column cursor (`h`/`l`, direct `1`–`4`); `Enter`/`o` opens the focused skill entry via the existing `lsa:open` bridge command; `A` triggers global add; `m`/`.` opens the focused row's action menu with `j`/`k`/`Enter`/`Esc` menu navigation.
- **Visual feedback** — a visible line/row cursor and character caret, rendered additively (extra classes/spans) so the DOM structure the self-test probes is untouched.
- **Toolbar hint text** — updated to advertise the keyboard layer and the `?` overlay.
- No Python-side behavior change: every keyboard action maps onto an existing bridge command; the practice-page visual selection is realized as a programmatic DOM selection so the existing `lsa:sel` → `dialog.selection` → `lsa:extract` path serves it unchanged.

## Capabilities

### New Capabilities

(none — this extends two existing capabilities)

### Modified Capabilities

- `openspec/specs/practice-hub/spec.md`: new requirement — vim-style keyboard navigation on the article-list page (row/skill/menu cursors, add, keymap overlay, focus rendering).
- `openspec/specs/practice-dialog/spec.md`: new requirement — vim-style keyboard navigation on the practice page (line and character cursors, visual selection driving extract, keyboard reveal and TTS playback, back/cancel/overlay keys).

## Impact

- `language_study_anki/web/practice.html` — keyboard layer JS + cursor/selection CSS + updated hint and contract comment (~150 lines added).
- `language_study_anki/web/list.html` — keyboard layer JS + focus CSS + updated contract comment (~90 lines added).
- `language_study_anki/*.py` — no changes; bridge command surface and selection contract are reused as-is.
- `tests/` — existing static/self-test probes keep passing (structure is only extended, never restructured); new self-test checks simulate key events for the primary keyboard flows.
- AnkiWebView key handling — the design uses only plain keys (letters, digits, `Enter`, `Esc`, `?`) because Anki's web view may intercept Ctrl-based combinations; the one interception risk (`Esc`) has a redundant alternative (`q`).
