## 1. Pure provisioning helpers

- [x] 1.1 Add `missing_items(col, scope)` to
  `language_study_anki/provisioning.py` — scope `"article"` → `LSA-Article`,
  scope `"extract"` → `@Basic`/`@EnListen`/`@EnSpeak` + deck `English`; no
  aqt imports — verify with the unit tests in 5.1
- [x] 1.2 Add `build_confirm_message(missing)` (pure string builder listing
  exactly the missing items) — verify with the unit tests in 5.1

## 2. Two-stage provisioning core

- [x] 2.1 Split provisioning by scope (keep `provision(col)` as the full
  idempotent entry for the self-test) and remove `ARTICLE_DECK`, the
  article-deck creation, and the `article_deck_id` return key — verify
  `python -c "import language_study_anki.provisioning"` succeeds and
  `provision()` no longer returns `article_deck_id`
- [x] 2.2 Retarget the five self-test references (`selftest_checks.py` ×3,
  `selftest_dialog_checks.py` ×2) from `ARTICLE_DECK`/`article_deck_id` to an
  existing deck — verify `grep -rn "ARTICLE_DECK\|article_deck_id"
  language_study_anki/` returns nothing and the suite passes (task 6.3)

## 3. Confirm-and-provision UI + startup wiring

- [x] 3.1 Create `language_study_anki/provisioning_ui.py` with
  `ensure_provisioned(col, parent, *, scope, context)` per design D2/D3
  (aqt imported lazily inside functions; `LSA_SELFTEST` auto-accepts without
  a dialog) — verify it imports without `aqt` installed:
  `python -c "import language_study_anki.provisioning_ui"`
- [x] 3.2 Add `register()` appending `gui_hooks.profile_did_open`
  (article scope only) and call it from `__init__.init()`'s aqt branch —
  verify in scratch Anki per task 6.1

## 4. Extract-time confirmation

- [x] 4.1 In `language_study_anki/extract.py`, replace the direct
  `provision(col)` with `ensure_provisioned(..., scope="extract", ...)`; on
  decline show a short info message and return before `col.new_note` (spec:
  practice-extract → Missing note types declined during extraction) —
  verify per task 6.2

## 5. Unit tests and docs

- [x] 5.1 Add `tests/test_provisioning.py` covering `missing_items` for both
  scopes (nothing missing / partial / all missing) and `build_confirm_message`
  (lists missing items, omits present ones) — verify
  `python -m unittest discover -s tests -t .` passes with the new tests
- [x] 5.2 Update `README.md`: drop the dedicated-deck claim and the
  "provisioned on first use" wording; describe the two-stage confirmed flow —
  verify the README no longer mentions a dedicated article deck or
  unattended provisioning

## 6. In-Anki verification (spec scenarios)

- [x] 6.1 Fresh scratch profile (`tools/scratch-anki.sh --fresh`, fully
  automatic via the prefs snapshot): profile open shows exactly one confirmation
  listing **only `LSA-Article`**; accept → type created with the eight
  spec'd fields (`Title` sort field), **no `Articles` deck created**;
  reopen profile → no dialog (article-storage: First use on a clean
  collection / Nothing missing at profile open / Existing note types are
  adopted)
- [x] 6.2 First extraction on that profile: confirmation lists **only
  `@Basic`, `@EnListen`, `@EnSpeak`, `English`**; accept → Add dialog opens
  with the prefilled note; decline → cancelled, no note (article-storage:
  Extract targets created at extraction time / Extract-time confirmation
  declined; practice-extract: Missing note types declined during
  extraction). Declined startup confirmation re-offered at the next profile
  open (article-storage: Startup confirmation declined)
- [x] 6.3 Run the self-test suite (`LSA_SELFTEST=1 LSA_SELFTEST_KEEP=1
  tools/scratch-anki.sh`): all checks pass with no dialog blocking the
  harness (article-storage: Headless self-test runs unattended)
