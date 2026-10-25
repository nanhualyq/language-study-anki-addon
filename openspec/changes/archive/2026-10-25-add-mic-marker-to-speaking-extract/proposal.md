## Why

Speaking-mode extracts and reading-mode extracts produce byte-identical
`Front` shapes (context lines + selection wrapped in `<mark>`), so a speaking
card is visually indistinguishable from a reading card in the browser card
list and during review. A visible 🎤 decoration inside the mark makes
speaking cards instantly recognizable — as a review-time cue ("say this
aloud") and as a browser filter (`Front:🎤`).

## What Changes

- Speaking extracts decorate the marked selection in `Front`:
  `<mark>🎤selected🎤</mark>` (emoji inside the mark, as prefix and suffix of
  the selected text).
- All other modes (reading, writing, listening), the `Back`/`Phone`/`Title`/
  `Url` fields, dictionary lookup, and the hidden timestamp are untouched.
- Applies to extracts performed after the change only; already-extracted
  notes are not migrated.
- `build_front()` gains optional decoration parameters (default: no
  decoration) so the speaking-specific behavior stays a caller decision.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `practice-extract`: the Speaking entry of "Prefilled note content" — the
  selection in `Front` is wrapped in `<mark>` **with 🎤 as prefix and suffix
  of the selected text inside the mark**; the "Speaking shows the selection"
  scenario is updated accordingly. No other mode's requirements change.

## Impact

- `language_study_anki/field_builder.py` — `build_front()` signature
  (additive, optional parameters; defaults preserve current output).
- `language_study_anki/extract.py` — speaking branch passes the 🎤
  decoration.
- `tests/test_field_builder.py` — new unit tests for the decoration and for
  the unchanged-default regression.
- `language_study_anki/selftest_dialog_checks.py` — speaking extract round
  asserts the decoration (extract-log token / Front content check).
- No note types, decks, field names, or stored-article data change; no
  user-facing settings are added.
