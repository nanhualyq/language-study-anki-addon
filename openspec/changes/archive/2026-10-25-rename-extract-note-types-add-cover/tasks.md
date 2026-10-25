## 1. Rename the extract note types

- [x] 1.1 In `language_study_anki/provisioning.py`, change `EXTRACT_NOTE_TYPES` to `["LSA-ReadWrite", "LSA-Listen", "LSA-Speak"]`, `AUDIO_EXTRACT_NOTE_TYPES` to `("LSA-Listen", "LSA-Speak")`, and `MODE_NOTETYPE` to map reading/writing → `LSA-ReadWrite`, listening → `LSA-Listen`, speaking → `LSA-Speak`; verify by importing the module and asserting the three constants hold the new values
- [x] 1.2 Update the stale note-type names in the `provisioning.py` module docstring (extract scope line) and the `extract.py` module docstring (per-mode table), and in the `ensure_extract_notetype` docstring's decoy note; verify `grep -rn "@Basic\|@EnListen\|@EnSpeak" language_study_anki` returns no matches

## 2. Cover field on extract types and extraction copy

- [x] 2.1 Append `"Cover"` to `EXTRACT_FIELD_NAMES` in `provisioning.py` (order `Front`, `Back`, `Title`, `Url`, `Cover`), giving both fresh creation and the existing additive repair of adopted types the field; verify with a unit test that `required_extract_fields("LSA-ReadWrite")` includes `Cover` and that `required_extract_fields("LSA-Listen")` includes `Cover` and `Phone`
- [x] 2.2 In `extract.py` `_open_add_dialog`, add `("Cover", <defensive article read, empty when absent>)` to `field_values` so Cover is copied alongside `Title`/`Url` in every mode; verify no `KeyError` path is introduced when the article lacks the field (defensive `.get`-style read)

## 3. Unit tests

- [x] 3.1 Update `tests/test_provisioning.py` to the new names (missing-items expectations, confirmation-message assertions) and add/adjust assertions for the `Cover` requirement; verify `python -m unittest tests.test_provisioning` passes
- [x] 3.2 Update `tests/test_browser_menu.py` fake note type names that reference `@Basic` to a new-name equivalent; verify `python -m unittest tests.test_browser_menu` passes
- [x] 3.3 Add a unit test that an adopted extract type missing `Cover` has it added additively (mirroring the existing decoy-repair test); verify it passes with `python -m unittest discover -s tests -t .`

## 4. In-addon selftest

- [x] 4.1 In `language_study_anki/selftest_checks.py`, rename the decoy-planted type (`@EnSpeak` → `LSA-Speak`, including the marker-field comment) and the `prov["extract_notetypes"]["@Basic"]` key to `LSA-ReadWrite`; verify `grep -n "@Basic\|@EnListen\|@EnSpeak" language_study_anki/selftest_checks.py` returns nothing
- [x] 4.2 In `language_study_anki/selftest_dialog_checks.py`, update `EXTRACT_ROUNDS` note-type entries and the `prov["extract_notetypes"]["@Basic"]` usage to the new names; verify `grep -n "@Basic\|@EnListen\|@EnSpeak" language_study_anki/selftest_dialog_checks.py` returns nothing
- [x] 4.3 Extend the selftest extract check so the article model used for extraction carries a `Cover` field with a value (simulating the user-maintained field) and the extracted note's `Cover` equals it, plus an empty-fallback round for an article without the field; verify the new assertions appear in the extract round results
- [x] 4.4 Run the full in-addon selftest `LSA_SELFTEST=1 LSA_SELFTEST_KEEP=1 tools/scratch-anki.sh` and verify every check in `.scratch-anki/selftest-results.json` has `"ok": true`, including provisioning (a clean collection gets `LSA-ReadWrite`/`LSA-Listen`/`LSA-Speak` with a `Cover` field) and all four extract modes using the new note types

## 5. Documentation and final sweep

- [x] 5.1 Update `README.md`: the provisioning paragraph and the per-mode extraction table use `LSA-ReadWrite`/`LSA-Listen`/`LSA-Speak`, and the article/extract field mentions include `Cover` on extract types; verify by re-reading the rendered sections
- [x] 5.2 Final sweep: `grep -rn "@Basic\|@EnListen\|@EnSpeak" language_study_anki tests tools README.md` returns no matches (only `openspec/specs/` keeps the old names until the change is archived/synced), and `python -m unittest discover -s tests -t .` passes
