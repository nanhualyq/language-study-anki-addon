## Why

Learned (studied) lines in the practice dialog are currently highlighted with a green background tint (`.line.learned { background: #f2f9f2 }` plus a green line-number color), which draws attention to rows the user has already covered. The user wants studied lines to visually recede instead: fade the whole row via reduced opacity and drop the green tint entirely.

## What Changes

- Change the learned-line appearance in the practice dialog from a green background/line-number highlight to a whole-row fade: learned rows render with reduced CSS `opacity`, so text, line numbers, and row controls all appear de-emphasized.
- Remove the green styling (`.line.learned` background `#f2f9f2` and `.ln` color `#4a4`); learned rows are distinguished from unlearned rows only by their lower opacity.
- Keep the `learned` CSS class, class-application logic, scroll restore, and live `markLearnedUpTo` update unchanged — only the visual treatment changes.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `practice-dialog`: The "Scroll position restore" requirement's learned-line styling clause is tightened: lines at or below the stored progress position SHALL be visually de-emphasized by rendering the row at reduced opacity, and SHALL NOT use a distinct highlight color/background (the current green tint is removed).

## Impact

- `language_study_anki/practice_dialog.py` — the `_HTML` template's `<style>` block (`.line.learned` rules) only.
- `language_study_anki/selftest_dialog_checks.py` — checks count `.line.learned` elements only; unaffected as long as the class remains (it does).
- No changes to progress tracking, extract flow, scroll restore, or the `learned` class logic in the template's JS.
- Main spec `openspec/specs/practice-dialog/spec.md` gains the tightened learned-line styling wording after sync.
