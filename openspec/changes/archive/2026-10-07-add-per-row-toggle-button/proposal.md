## Why

In the practice dialog, hidden line content (Listening's source text, Writing's
source line) is revealed by clicking anywhere on the row. The row is also the
text-selection surface, so a plain click meant to place the caret, start a
selection, or stop a drag routinely shows/hides the line by accident — content
the user was reading disappears under the cursor. A `<details>`-style
disclosure control makes revealing an explicit, single-purpose action that
cannot be triggered by touching the text.

## What Changes

- Every line gains an explicit per-row toggle button (chevron, `▸`/`▾`) that
  reveals or hides that line's hidden content; it is the only control that
  changes a line's visibility.
- Clicking a row — its text, its padding, anywhere except a button — never
  shows or hides content; clicks only start selections. The former
  row-click toggles in Listening (`expanded`) and Writing (`revealed`) and
  their selection-guard workarounds are removed.
- Per-mode reveal targets: Listening → source text, Writing → source line
  (translation already visible), Reading → translation line, Speaking →
  translation line (newly revealed on demand instead of never shown).
- Reading's toolbar "Show translation" button now opens/closes every row
  through the same per-row state, so the global button and individual
  chevrons cannot disagree.
- Lines with nothing hidden (empty translation/source) render an invisible
  placeholder of the same width, keeping every line's text aligned.
- Self-test `dialog_modes` and the four-mode extract check are updated to
  click the toggle button, and now also assert that a plain row click does
  not change visibility.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `openspec/specs/practice-dialog/spec.md`: "Mode-specific line rendering"
  changes from an implicit row-click/toolbar reveal to an explicit per-line
  toggle control; a new requirement covers the reveal control itself
  (explicit control only, no row-click toggling, global/per-row consistency,
  alignment placeholder).

## Impact

- `language_study_anki/practice_dialog.py` — the embedded dialog HTML/CSS/JS
  (`_HTML`): `.twisty` control, `.line.open` mode rules, `setOpen()`,
  reworked `#trans-toggle` and `app` click handlers.
- `language_study_anki/selftest_dialog_checks.py` — `_JS_READING`,
  `_JS_LISTENING`, `_JS_WRITING`, `_JS_SPEAKING`, their `_ev_*` evaluators,
  and the extract round's reveal JS.
- No Python bridge commands, note fields, progress semantics, storage format,
  or extract behavior change; `Ctrl+E`, selection capture, TTS, scroll
  restore and learned styling are untouched.
- Users lose the row-click shortcut for revealing a line (intentional, that
  is the point of the change).
