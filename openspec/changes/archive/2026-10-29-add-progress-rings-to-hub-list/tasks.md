# Tasks: add-progress-rings-to-hub-list

## 1. list.html ring rendering

- [x] 1.1 Replace the pill-button CSS for `.skill` with the vertical ring cell
      (`.skill`, `.ring`, `.pct`, `.name`; ring 40px, accent `#3b82f6`, track
      `#e3e3e5`, hover tint) and verify the template still parses as valid
      HTML (open in a browser or `python -c` string check).
- [x] 1.2 Rewrite the JS skill-entry builder to emit the SVG ring + centered
      `.pct` + `.name` per design D1/D3, computing
      `stroke-dashoffset = C * (1 - pct/100)` with C from `r=15.5`, keeping
      `data-open="<id>:<mode>"` and the delegated click handler unchanged;
      verify by rendering `list_html(...)` with fixture rows in the scratch
      Anki instance and eyeballing 0% / partial / 100% rows.
- [x] 1.3 Update the contract comment at the top of `list.html` (entry layout
      description) and verify it no longer claims entries show
      `"<Skill> <pct>%"` text.

## 2. Contract sync: self-test + unit test

- [x] 2.1 Update `selftest_dialog_checks.py` hub list probe: read `.pct` and
      `.name` text per `.skill` instead of whole-button `textContent`, and
      split the expected `f"{label} {pct}%"` strings accordingly (including
      the post-extract `"Reading 100%"` update); verify the module still
      imports (`python -c "import language_study_anki.selftest_dialog_checks"`
      fails only on aqt import outside Anki - syntax check via
      `python -m py_compile`).
- [x] 2.2 Update `tests/test_hub.py` static assertion: replace the
      `' ' + pct + '%</button>'` format check with ring-markup checks
      (`class="ring"`, `stroke-dashoffset`, `.pct`, `.name`) and verify
      `python -m unittest tests.test_hub` passes.

## 3. Verification

- [x] 3.1 Run the full unit suite: `python -m unittest discover -s tests -t .`
      and verify all tests pass.
- [x] 3.2 Run the in-Anki self-test
      (`LSA_SELFTEST=1 LSA_SELFTEST_KEEP=1 tools/scratch-anki.sh`) and verify
      the hub list check passes with rings rendering at 0/partial/100 and
      navigation still working.
