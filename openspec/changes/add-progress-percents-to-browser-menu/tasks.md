## 1. Percent helper

- [x] 1.1 Add a `_progress_percent(note, skill) -> int` helper in `language_study_anki/browser_menu.py` (progress via `get_progress`, line count via `field_to_lines(note["Content"])`, half-up rounding, clamp 0–100, 0% for empty `Content`) and verify with unit tests covering: exact 25% (10/40 lines), 0% (no progress), empty content → 0%, progress past line count → 100%, negative/garbage progress → 0%
- [x] 1.2 Extend `tests/test_progress.py`-style coverage with a new `tests/test_browser_menu.py` exercising the helper through `build_menu_labels` with a fake `col`, verifying `python -m unittest tests.test_browser_menu` passes

## 2. Menu label assembly

- [x] 2.1 Update `build_menu_labels` to append ` (<percent>%)` to each `MODE_LABELS` label using the **first** selected note, keeping article-only gating (`None` for empty/mixed/non-article selections) unchanged, and verify the unit tests assert labels like `Practice: Reading (25%)` while non-article/mixed/empty selections still return `None`
- [x] 2.2 Verify the hook path still opens the dialog for the first selected note and the menu renders suffixes: run the addon self-test `check_browser_menu` (see task 3.1 for its update)

## 3. Existing checks and specs

- [x] 3.1 Update `language_study_anki/selftest_dialog_checks.py::check_browser_menu` — its `expected` list now includes percentage suffixes (derive expected percentages from the fixture article's `Content` line count and progress fields rather than hard-coding), and verify the in-Anki self-test reports `ok: true`
- [x] 3.2 Run `openspec validate --change "add-progress-percents-to-browser-menu"` and the full unit suite (`python -m unittest discover tests`) and verify both pass
