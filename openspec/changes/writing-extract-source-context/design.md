## Context

Writing-mode extraction (`language_study_anki/extract.py`, `_open_add_dialog`) builds `Front` with `build_front(translations, line_no, start, end)` — the up-to-3 context lines *and* the marked current line all come from the translation list — while `Back` is the source line at the same index. `build_front` (`language_study_anki/field_builder.py`) derives context from the same list it takes the current line from. The practice dialog already pairs source and translation lines by index (`D.lines[i-1]` ↔ `D.translations[i-1]`), which is the same assumption `Back` already relies on. See proposal.md for motivation.

Interpretation of the request (recorded assumption): "当前行不变" means the `Front`'s marked current line stays the **translation line**; only the lines above it switch to source lines. Making the whole `Front` source-based would print the answer, since `Back` is the source line at the same index.

## Goals / Non-Goals

**Goals:**
- Writing `Front` context lines (up to 3 above, `<br>`-terminated) come from the article's source (原文) lines.
- Writing `Front` current line, `<mark>` selection, hidden timestamp, `Back`, note type, and no-lookup behavior stay exactly as they are.
- Reading / Listening / Speaking fronts byte-identical to today (regression-guarded by existing tests).

**Non-Goals:**
- Changing the practice dialog's Writing-mode display or selection model (selection stays on the translation).
- Migrating already-saved notes (extract-time construction only, consistent with prior field-format changes).
- Reference-app parity for this detail — the source-line context is an intentional deviation.
- Changing `Back`, lookup, progress, provisioning, or field names.

## Decisions

- **D1: Extend `build_front` with an optional context-source list instead of assembling the Writing front in `extract.py`.** New keyword-only parameter (e.g. `context_source: list[str] | None = None`); when omitted, behavior is unchanged (context from the current-line list), so the other three modes and every existing test keep passing. Writing passes `context_source=lines` (source) while the primary list stays `translations`. Alternative considered: build the Writing front by hand in `extract.py` — rejected: it would duplicate `html.escape`, `<mark>`, `<br>`, and hidden-timestamp logic in a second place.
- **D2: Index semantics for the context source.** The1-based line number keeps its meaning; context indices are `max(0, line_no-1-CONTEXT_LINES) … line_no-2`, additionally clamped to `len(context_source)` (a shorter source list yields fewer context lines, never an error). The current-line range check and selection-bounds check keep validating against the primary list (translations), exactly as today.
- **D3: `extract.py` Writing branch changes by one argument.** `front = build_front(translations, line_no, start, end, context_source=lines)`; the translations range check, `back = lines[line_no - 1]`, and the log tokens `front:translation back:source-line highlight:mark` stay unchanged. Those tokens are subset-asserted by the in-Anki self-test (`EXTRACT_ROUNDS`) and remain accurate (the front's current line is still the translation).
- **D4: Verification stays unit-level for content.** `tests/test_field_builder.py` gains cases asserting the source-context front: mid-article context lines come from the source list (and no translation context lines), near-top clamping, first line has no context, escaping of context lines, and unchanged output when `context_source` is omitted. The existing Writing self-test round continues to cover branch, note type, cover, and progress end-to-end.

## Risks / Trade-offs

- [Mixed-language `Front` (原文 context directly above a 译文 current line) reads abruptly] → This is the requested behavior; separators and layout are unchanged, so only line content differs.
- [Source and translation lists differ in length in malformed articles] → Context is clamped to the available source lines (D2); `Back`'s existing same-index assumption is untouched, so no new failure mode is introduced.
- [Users may expect already-created Writing notes to update] → No migration by design (consistent with `phone-multiline-phonetics`, `add-mic-marker`); new content applies to new extractions only — call this out in the summary.
- [Hidden-timestamp uniqueness and `<mark>` offsets unchanged] → No interaction: the timestamp span and selection bounds are computed from the primary list as before.

## Migration Plan

None: extract-time construction only. Rollback = revert the code change; notes created meanwhile remain valid.

## Open Questions

None.
