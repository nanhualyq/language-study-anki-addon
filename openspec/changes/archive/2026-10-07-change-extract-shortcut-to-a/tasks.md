## 1. Shortcut handler

- [x] 1.1 In `language_study_anki/practice_dialog.py`, change the `keydown` listener to trigger `pycmd('lsa:extract')` only when `e.key` is `a`/`A` and none of `ctrlKey`/`metaKey`/`altKey`/`shiftKey` are set (removing the `Ctrl+E`/`Meta+E` branch), and verify by reading the updated handler block that `Ctrl+E` and `Ctrl+A` can no longer match
- [x] 1.2 Update the in-dialog hint line to `select text &amp; press a to extract` and verify no `Ctrl+E` string remains in `practice_dialog.py` (`rg -n "Ctrl\+E|ctrlKey" language_study_anki/practice_dialog.py` shows only the new modifier-gating check)

## 2. Docs and code comments

- [x] 2.1 Update the `Ctrl+E` references in `README.md` (feature bullet) and the `run_extract` docstring in `language_study_anki/extract.py` to describe the bare `a` shortcut, and verify with `rg -n "Ctrl\+E" README.md language_study_anki/` returns no matches

## 3. Self-test

- [x] 3.1 In `language_study_anki/selftest_dialog_checks.py`, change the simulated keydown payload in `check_extract_all_modes` from `{key:'e',ctrlKey:true,…}` to `{key:'a',…}` (no modifier flags), update the "fire Ctrl+E" docstring wording, and verify the payload contains no modifier keys

## 4. Verification

- [x] 4.1 Run `python -m unittest discover -s tests -t .` and verify all unit tests pass
- [x] 4.2 Run the in-addon self-test (`LSA_SELFTEST=1 LSA_SELFTEST_KEEP=1 tools/scratch-anki.sh`) and verify the four-mode extraction check passes with the new key
- [x] 4.3 Manually open the practice dialog, select text, press `a` → Add dialog opens; press `Ctrl+E` and `Ctrl+A` with a selection → nothing happens; press `a` with no selection → nothing happens (matches spec scenarios in `specs/practice-extract/spec.md`)
