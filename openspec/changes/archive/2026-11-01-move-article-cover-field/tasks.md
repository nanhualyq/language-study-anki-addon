## 1. Provisioning field order

- [x] 1.1 Reorder `ARTICLE_FIELDS` in `language_study_anki/provisioning.py` so `Cover` is index 1 (`Title, Cover, Content, Translation, Url, ProgListening, ProgSpeaking, ProgReading, ProgWriting`), and update the comment above it to say existing collections are aligned manually via Anki's Fields dialog (no addon-side migration); verify with `python -c "from language_study_anki.provisioning import ARTICLE_FIELDS; assert ARTICLE_FIELDS[:2] == ['Title', 'Cover'] and ARTICLE_FIELDS[-1] == 'ProgWriting'"`

## 2. Tests

- [x] 2.1 Update the `test_article_parity` expected field order in `tests/test_provisioning.py` to the new order; verify with `python -m unittest tests.test_provisioning -v` (all tests pass, parity test asserts `Cover` second)

## 3. Stale docstring cleanup

- [x] 3.1 Fix the docstring of `_ensure_article_cover_field` in `language_study_anki/selftest_dialog_checks.py`: remove the claim that the addon does NOT provision `Cover` on articles (contradicts `provisioning.py`), keep the guard behavior unchanged; verify with `grep -n "does NOT provision" language_study_anki/selftest_dialog_checks.py` returning no matches

## 4. Full verification

- [x] 4.1 Run the full unit suite `python -m unittest discover -s tests -t .` and confirm everything passes (no runtime code depends on field order — this proves the reorder is transparent)
