## 1. `build_front` 支持独立的上下文来源

- [x] 1.1 In `language_study_anki/field_builder.py`, add keyword-only `context_source: list[str] | None = None` to `build_front`: context indices `max(0, current-CONTEXT_LINES) … current-1` are read from `context_source` (clamped to its length, `None` ⇒ current behavior) while the current line, `<mark>` selection, and hidden timestamp still come from `lines` — verify with `python -m py_compile language_study_anki/field_builder.py` plus `python -m unittest tests.test_field_builder` (all existing cases pass unchanged, proving default behavior is byte-identical).

## 2. Writing 提取接线

- [x] 2.1 In `language_study_anki/extract.py` `_open_add_dialog`, change the Writing branch to `front = build_front(translations, line_no, start, end, context_source=lines)`, keeping the translations range check, `back = lines[line_no - 1]`, and log tokens `front:translation back:source-line highlight:mark` unchanged — verify with `python -m py_compile language_study_anki/extract.py` and a code walkthrough showing the Reading/Listening/Speaking branch and `kinds` strings untouched.

## 3. 单元测试

- [x] 3.1 Add cases to `tests/test_field_builder.py` covering the source-context front: mid-article (line 7 ⇒ source lines 4–6 `<br>`-terminated above the marked line 7, no translation context lines), near-top clamping, first line has no context, `context_source` lines escaped, and `context_source=None` reproduces the old output — verify with `python -m unittest tests.test_field_builder`.

## 4. 规格与自测一致性

- [x] 4.1 Run `openspec validate --all` and verify the change `writing-extract-source-context` validates with no errors.
- [x] 4.2 Verify the in-Anki self-test contract by walking `EXTRACT_ROUNDS`' Writing tokens (`front:translation`, `back:source-line`, `lookup:skipped`) against the unchanged log strings in `extract.py` (subset assertion in `check_extract_all_modes`) — the full `LSA_SELFTEST=1 tools/scratch-anki.sh` run is approval-gated and is not executed as part of this task.
