## Context

`browser_menu.build_menu_labels(note_ids, col)` is a pure function that currently returns four static `(mode, "Practice: <Skill>")` pairs after verifying every selected note is an `LSA-Article`. Labels are consumed by the `browser_will_show_context_menu` hook, which opens the dialog for the **first** selected note. Per-skill progress lives in `ProgListening/ProgSpeaking/ProgReading/ProgWriting` as 1-based last-extracted line numbers (`progress.get_progress`); total lines come from `storage.field_to_lines(note["Content"])`. See proposal.md for motivation and `specs/practice-dialog/spec.md` for the exact behavior contract.

## Goals / Non-Goals

**Goals:**
- Show an integer percentage per skill in the four menu labels, computed for the first selected note.
- Keep `build_menu_labels` pure and unit-testable; no new I/O paths or dependencies.

**Non-Goals:**
- Progress aggregation across multiple selected notes (average/min).
- Persisting percentages as new note fields, or showing percentages anywhere else (dialog, browser columns).
- Changing the progress write path (decision D8 untouched: extraction remains the only writer).

## Decisions

- **Percentage derived, not stored**: `round(progress / line_count * 100)` computed at menu-build time from `Content`. Alternative rejected: storing a percentage field — it would duplicate the source of truth, require migration, and drift when content edits change the line count. Cost: `field_to_lines` runs once per menu open on the first note only (first note is already fetched for the note-type check), which is negligible for realistic article sizes.
- **First-note semantics**: percentages describe `note_ids[0]`, the same note the clicked action opens, so the label never disagrees with the dialog behind it. Alternative rejected: per-note labels in a multi-selection are impossible (one shared item per skill), and averages are misleading for a "what will I open" affordance.
- **Rounding & clamping in one place**: a small helper (e.g. `_progress_percent(note, skill) -> int`) does `max(0, min(100, round(...)))` with a zero-line guard returning `0`. Python's `round` uses banker's rounding; spec only requires "nearest whole number", so either is conformant — pick `int(x + 0.5)` on the clamped ratio for deterministic half-up behavior in tests. Progress past the end of the (possibly shortened) article clamps to 100%, mirroring the dialog's clamped scroll restore.
- **Label assembly stays in `build_menu_labels`**: `f"{label} ({pct}%)"` appended to the existing `MODE_LABELS` strings; `MENU_ITEMS` constants alone no longer suffice, so the function derives items from the first note. The article-only gating (`None` for mixed/non-article/empty selection) is unchanged and evaluated first.

## Risks / Trade-offs

- [Existing tests assert static labels] → `selftest_dialog_checks.check_browser_menu` compares against `expected` without suffixes; update it to expect percentages (it builds the article via `_ensure_long_article`, so line counts are known at assertion time — compute expected values from the same helper inputs or assert with a regex/parse).
- [Banker's vs half-up rounding surprises in tests] → fix half-up in the helper and assert exact values in unit tests with crafted progress/line counts.
- [Malformed progress or missing fields] → `get_progress` already returns 0 on bad input; `field_to_lines` on a missing/empty `Content` yields `[]` → 0%.
