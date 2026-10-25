## 1. Article note type: Cover field + explicit CSS

- [x] 1.1 Add `"Cover"` to `ARTICLE_FIELDS` in `language_study_anki/provisioning.py` (9 fields, `Cover` last) and set the explicit production `.card` CSS (with `line-height: 1.5;`) on the model in `_create_article_model`; verify a freshly created `LSA-Article` model has the 9 fields ending in `Cover`, `sortf` = Title, and the CSS applied.

## 2. Extract field order + sticky

- [x] 2.1 Encode the production field order — non-audio `Front, Back, Url, Title, Cover`; audio `Front, Back, Phone, Url, Title, Cover` (`Phone` third) — plus the sticky set (`Front`, `Back`, `Url`, `Title` sticky; `Phone`/`Cover` not), and make `required_extract_fields(name)` return the ordered production list; verify `required_extract_fields("LSA-ReadWrite") == ["Front","Back","Url","Title","Cover"]` and `required_extract_fields("LSA-Listen") == ["Front","Back","Phone","Url","Title","Cover"]`.

## 3. Extract templates, CSS, browser template, sort field

- [x] 3.1 Add per-type template constants (`qfmt`/`afmt`/`bqfmt` verbatim from the design's production reference), the shared extract `.card` CSS, and `sortf` = Front; rework `_create_extract_model` to add fields in production order with sticky flags and apply the templates, CSS, and browser question template; verify a freshly created `LSA-Listen` model carries the production `qfmt`/`afmt`/`bqfmt`, the CSS, sticky `Front`/`Back`/`Url`/`Title`, and `sortf` = Front.

## 4. Parity unit test

- [x] 4.1 Add a unit test in `tests/test_provisioning.py` that constructs all four note types via a fake model manager and asserts field order, sticky flags, `qfmt`/`afmt`/`bqfmt`, CSS, and sort field equal the production-captured reference strings (hardcode the 2026-10-25 production values as the expected literals); verify with `python -m unittest tests.test_provisioning`.

## 5. Selftest + end-to-end verification

- [x] 5.1 Reconcile `language_study_anki/selftest_checks.py` (decoy plant / provision-adoption expectations) with the reordered `EXTRACT_FIELD_NAMES` and the now-provisioned Article `Cover`, changing only assertions that depend on order or the old 8-field Article; verify the provisioning self-check still asserts correctly. (No change needed: the provision check uses a subset field test and `sortf == 0`, both order-independent; confirmed by the selftest run.)
- [x] 5.2 Run the full in-addon selftest on a fresh base `LSA_SELFTEST=1 LSA_SELFTEST_KEEP=1 tools/scratch-anki.sh --fresh` and verify every check in `.scratch-anki/selftest-results.json` has `"ok": true`.
- [x] 5.3 Run `python -m unittest discover -s tests -t .` and confirm the whole suite passes (including the new parity test).
