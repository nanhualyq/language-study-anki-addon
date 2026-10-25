## 1. Core implementation

- [x] 1.1 Add optional `mark_prefix: str = ""` / `mark_suffix: str = ""` parameters to
      `build_front()` in `language_study_anki/field_builder.py`, concatenated inside the
      `<mark>` segment around the (escaped) selected text.
      Verify: existing `python -m unittest tests.test_field_builder -v` all pass unchanged
      (defaults keep output byte-identical).
- [x] 1.2 In `language_study_anki/extract.py`, add module constants
      `_SPEAKING_MARK_PREFIX = _SPEAKING_MARK_SUFFIX = "🎤"` and pass them to `build_front`
      when `mode == "speaking"` (all other modes keep the defaults).
      Verify: speaking extract produces `Front` containing `<mark>🎤…🎤</mark>`;
      reading/writing/listening `Front` contain no 🎤.
- [x] 1.3 In the same speaking branch, extend the `_log(dialog, f"fields {kinds} …")`
      kinds string with a `mark:mic` token (mirrors the existing `highlight:mark` style).
      Verify: the extract log for a speaking round contains `mark:mic`.

## 2. Unit tests

- [x] 2.1 Add a `tests/test_field_builder.py` case calling
      `build_front(..., mark_prefix="🎤", mark_suffix="🎤", timestamp_ms=1)` and assert the
      Front contains `<mark>🎤…🎤</mark>` around the selection; plus a case asserting the
      undecorated default output is unchanged.
      Verify: `python -m unittest tests.test_field_builder -v` passes with the new cases.
- [x] 2.2 Run the whole zero-dependency suite.
      Verify: `python -m unittest discover -s tests -t .` — all tests pass, no count
      regressions in existing files.

## 3. Self-test (in-Anki suite)

- [x] 3.1 In `language_study_anki/selftest_dialog_checks.py`, add `"mark:mic"` to the
      speaking row's required tokens in `EXTRACT_ROUNDS`.
      Verify: `LSA_SELFTEST=1 LSA_SELFTEST_KEEP=1 tools/scratch-anki.sh` — the
      `check_extract_all_modes` speaking round passes (`.scratch-anki/selftest-results.json`
      shows `"ok": true`), and the other three rounds still pass.
- [x] 3.2 (Scope addition, approved during apply) Fix a pre-existing self-test harness bug:
      `selftest.py`'s 90s startup watchdog — armed at addon load and only disarmed by a
      written results file — killed any suite longer than 90s mid-run with a misleading
      "STARTUP TIMEOUT: profile never opened". Fix: set a `_profile_opened` flag in
      `_on_profile_open()`; `startup_timeout()` returns early once the profile is open
      (the `_Runner`'s own WATCHDOG_MS/STEP_TIMEOUT_MS still cover a hung suite).
      Verify: task 3.1's self-test run completes and writes full per-check results
      instead of the startup-timeout stub.

## 4. Docs

- [x] 4.1 Update the extract-mode table in `README.md`: Speaking `Front` cell now reads
      `source + <mark>🎤…🎤</mark>`.
      Verify: README table matches the shipped behavior; `openspec validate --strict`
      on the change passes.
