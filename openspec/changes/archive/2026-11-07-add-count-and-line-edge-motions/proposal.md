## Why

The practice page's in-line cursor only moves one step per keystroke (`h`/`l`/`w`/`b`/`e`), so covering any wider span means hammering the key many times; there is also no way to jump to the line's start or end at all. Vim users already have the muscle memory for a count prefix (`3w`, `10l`) and `0`/`$`, and the same gap applies while extending a visual selection — growing or shrinking a selection across a long span is equally tedious.

## What Changes

- Add a **count prefix** for in-line motions: digits `1`–`9` start a count, `0` continues it while a count is pending (`10l`), and the pending count is consumed by `h`/`l`/`w`/`b`/`e`.
  - Count applies ONLY to in-line keys. `j`/`k`/`gg`/`G`/`PageUp`/`PageDown` ignore a pending count (the count is discarded and the key behaves as it does today).
  - The pending count is shown as a small badge and auto-expires after ~1s of inactivity, so a stray digit never causes a surprise jump later.
- Add **line-edge motions**: bare `0` moves the character cursor to the line start, `$` to the line end (absolute positions; they do not take a count).
- Both features work in the two existing movement contexts identically: plain cursor movement, and while a visual selection is active (the motion extends the selection through the existing `extendVisual()` path).
- Extend the `?` keymap overlay so the new keys are discoverable.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `practice-dialog`: "Line cursor and keyboard movement" gains count-prefixed in-line motion, `0`/`$` line-edge motions, and pending-count badge/expiry scenarios; "Keyboard text selection and extract" gains the count/line-edge selection-extension scenarios; "Keyboard return and keymap help" documents the new keys in the keymap overlay.

## Impact

- `language_study_anki/web/practice.html` — keydown handler (digit/`0`/`$` branches, pending-count state), `moveCol()`/`moveWord()` count support, badge element/CSS, `?` overlay content.
- `language_study_anki/selftest_dialog_checks.py` — `check_keyboard_nav` gains synthetic-key assertions for count, `0`/`$`, count expiry, and selection extension.
- No Python bridge, storage, or extract-pipeline changes; no changes to list page keys.
