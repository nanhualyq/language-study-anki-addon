## 1. Implementation

- [x] 1.1 Change `format_phonetics()` in `language_study_anki/youdao.py` to
      join with `"<br>"` instead of `" "` and update its docstring: drop the
      "Flutter parity" claim, state the per-line format
      (`UK /…/<br>US /…/`) and that it is a deliberate divergence from the
      reference app. Verify: `python -c "from language_study_anki.youdao
      import format_phonetics as f; print(f([('UK','a'),('US','b')]))"`
      prints `UK /a/<br>US /b/`

## 2. Tests

- [x] 2.1 Update `tests/test_youdao.py::test_format_phonetics_flutter_parity`:
      rename to reflect the per-line contract and change the expected value
      to `"UK /a/<br>US /b/"`. Verify: the test passes
- [x] 2.2 Add edge-case unit tests: a single-region input yields no
      separator (`format_phonetics([("UK", "a")]) == "UK /a/"`) and an empty
      input yields `""`. Verify: both tests pass
- [x] 2.3 Run the full unit suite (`python -m unittest discover -s tests -t .`)
        and verify all tests pass with no regressions

## 3. Spec sync check

- [x] 3.1 Run `openspec validate "phone-multiline-phonetics"` and
      verify the change validates; the delta spec merges into
      `openspec/specs/practice-extract/spec.md` at archive time (no manual
      main-spec edit needed)
