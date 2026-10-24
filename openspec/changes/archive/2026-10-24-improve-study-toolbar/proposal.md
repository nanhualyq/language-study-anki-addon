## Why

The practice dialog's toolbar shows progress as `ProgReading:12` — a raw field name plus the learned line number with no total, so the user cannot see how much of the article remains. Meanwhile the selection hint ("select text & press a to extract") floats `position: fixed` at the bottom-right, permanently covering the corner of the article text on the last screen. Both reduce the readability of the study view.

## What Changes

- Toolbar progress display simplifies from `<field name>:<learned>` to `<learned>/<total>` (e.g. `12/50`), clamped to the article's current line count.
- The progress counter updates live when an extraction advances progress (currently it only refreshes on next open).
- The selection hint moves from a fixed bottom-right overlay into the toolbar's right end, so nothing overlaps the article body; the `a` key in the hint is rendered as a visually distinct keycap instead of plain text.
- **BREAKING** (UI affordance): Reading mode's global "Show translation" toolbar toggle is removed. The per-line reveal control remains the only way to reveal hidden per-line content, consistent with the other three modes.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `practice-dialog`: Add a toolbar requirement (progress counter format, live update, hint placement and keycap styling, no global translation toggle); narrow Reading mode's translation reveal from "single line and all lines at once" to per-line only.

## Impact

- Affected code: `language_study_anki/practice_dialog.py` — the `_HTML` template string (~15 lines of HTML/CSS/JS edits: `#pf` textContent, `markLearnedUpTo`, `.hint` → toolbar, `<kbd>` styling, removal of `#trans-toggle` markup/CSS/JS listener); `language_study_anki/selftest_dialog_checks.py` — the Reading-mode dialog check clicks `trans-toggle` and must be updated to match (design detail in tasks).
- Not affected: Python bridge commands, `progress.py`, `extract.py`, note types, stored fields, TTS. The `tests/` unit suite covers none of the changed UI text or selftest checks.
