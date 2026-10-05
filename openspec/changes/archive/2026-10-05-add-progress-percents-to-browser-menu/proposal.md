## Why

The Browser context menu's four skill entries ("Practice: Listening/Speaking/Reading/Writing") give no indication of how far along the selected article already is for each skill, so users must open each practice dialog just to check progress.

## What Changes

- The four context-menu entries gain a progress percentage suffix computed from the selected note's per-skill progress field, e.g. `Practice: Reading (100%)`.
- Percentage = last extracted line ÷ total lines of the article's `Content`, rounded to the nearest integer; `0%` when there is no progress or the content is empty.
- Percentages always describe the **first selected note** — the same note whose practice dialog opens when the item is clicked (also the value shown when multiple notes are selected).
- Base labels and selection gating (article notes only) are unchanged.

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `practice-dialog`: The "Browser context-menu entry" requirement is extended: menu item labels append the first selected note's per-skill progress percentage.

## Impact

- `language_study_anki/browser_menu.py` — `build_menu_labels` must read the first note's content and progress fields instead of returning static labels.
- `language_study_anki/progress.py`, `language_study_anki/storage.py` (`field_to_lines`) — reused as-is for reading progress / counting lines.
- `openspec/specs/practice-dialog/spec.md` — requirement text updated via delta spec.
- Tests under `tests/` for `build_menu_labels`.
