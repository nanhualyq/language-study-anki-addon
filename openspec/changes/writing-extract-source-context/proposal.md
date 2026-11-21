## Why

Writing-mode extraction currently builds the note's `Front` entirely from the **translation** lines, so the up-to-3 context lines above the tested line are also 译文. When reviewing the card, surrounding translation context gives little help reconstructing the 原文 answer; the user wants the surrounding context to be the article's original text (原文) instead.

## What Changes

- Writing-mode extract `Front`: the context lines above the current line (up to 3, `<br>`-terminated) are now taken from the article's **source (原文) lines** instead of the translation (译文) lines.
- The **current line of the `Front` is unchanged**: it stays the translation line with the selection wrapped in `<mark>` plus the hidden timestamp span (the prompt line remains 译文; only the lines above it change).
- Unchanged: `Back` = source line at the same index; no dictionary lookup in Writing mode; note type `LSA-ReadWrite`; hidden-timestamp uniqueness; `Title`/`Url`/`Cover`.
- Unchanged: Reading, Listening, and Speaking `Front` construction (context and current line both from source lines).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `practice-extract`: the **Prefilled note content** requirement's Writing bullet and its "Writing extracts the translation" scenario — Writing `Front` context lines now come from the source lines while the marked current line stays the translation line.

## Impact

- `language_study_anki/field_builder.py` — `build_front` needs a way to draw the context lines from a different line list than the current line (new optional keyword; default behavior unchanged for the other three modes).
- `language_study_anki/extract.py` — Writing branch passes the source `lines` as the context source while keeping the translation line as the current line; extract-log tokens (`front:translation back:source-line highlight:mark`) stay valid for the in-Anki self-test's subset assertion.
- `tests/test_field_builder.py` — new unit coverage for source-context fronts (mid-article, near-top, first line, escaping).
- `openspec/specs/practice-extract/spec.md` — synced via this change's delta spec.
- Already-saved notes are not migrated (extract-time construction only, matching prior field-format changes).
