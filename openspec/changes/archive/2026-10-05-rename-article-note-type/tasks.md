# Tasks: rename-article-note-type

## 1. Rename the note type

- [x] 1.1 Change `ARTICLE_NOTE_TYPE` in `language_study_anki/provisioning.py` from `"Article"` to `"LSA-Article"` and verify `grep -rn '"Article"' language_study_anki tests tools` returns no matches (the deck name `Articles`, template name `Article card`, and UI strings such as "Article content is empty" intentionally stay unchanged)
- [x] 1.2 Verify all consumers (`browser_menu.py`, `practice_dialog.py`, `suspension.py`, `selftest_checks.py`, `selftest_dialog_checks.py`) reference only the `ARTICLE_NOTE_TYPE` constant — grep shows no other hardcoded note-type name

## 2. Verification

- [x] 2.1 Run the unit suite `python -m unittest discover -s tests -t .` and verify all 53 tests pass
- [x] 2.2 Run the in-addon selftest `LSA_SELFTEST=1 LSA_SELFTEST_KEEP=1 tools/scratch-anki.sh` and verify every check in `.scratch-anki/selftest-results.json` has `"ok": true`, including provisioning (a clean collection gets an `LSA-Article` note type) and the browser-menu check (menu items appear for `LSA-Article` notes only)
