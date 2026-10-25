## 1. Extract the template

- [x] 1.1 Create `language_study_anki/web/practice.html` containing the `_HTML` template verbatim (byte-identical markup, CSS, JS, and rationale comments) — verify by diffing against the current string's content
- [x] 1.2 Add the contract header comment to `web/practice.html` (produced/consumed by `practice_dialog.py`; placeholders MODE and LSA_DATA named split as `__` + NAME + `__` so the literal tokens never appear in the comment — Python-side `str.replace` must not be able to corrupt it; bridge commands `lsa:sel:`, `lsa:extract`, `lsa:play:<n>`; callback `window.markLearnedUpTo`) — verify the comment exists and lists all six contract elements

## 2. Rewire practice_dialog.py

- [x] 2.1 Replace the `_HTML` string with a module-load read: `_TEMPLATE_PATH` resolved relative to `__file__`, read once into `_HTML`, `FileNotFoundError` message includes the resolved path — verify import succeeds and `_HTML` is a non-empty string starting with `<!DOCTYPE html>`
- [x] 2.2 Add the reverse contract comment at the loader and near `_on_bridge` (points to `web/practice.html`; same six contract elements) — verify comment present in both locations
- [x] 2.3 Delete the old `_HTML = r"""..."""` block — verify `practice_dialog.py` is under ~180 lines and `rg '_HTML = r'` finds nothing

## 3. Verify equivalence

- [x] 3.1 Run the existing test suite — `python -m unittest discover -s tests -t .` (README's runner; pytest not installed): 86/86 pass, no test edits needed
- [x] 3.2 Diff check: strip the contract header comment from the loaded template → byte-equal to the original `_HTML` string from git HEAD; substitution verified (`__MODE__` renders both body targets, `__LSA_DATA__` once, contract comment survives replace untouched). Note: the spec's "exactly once" wording was corrected — the original template legitimately contains `__MODE__` twice (body class + mode-name); the invariant verified is "only in body, none in the comment, identical to original"
- [x] 3.3 In-app smoke test via `LSA_SELFTEST=1 tools/scratch-anki.sh` (isolated ANKI_BASE, never touches production): all 11 self-test checks ok — `dialog_modes` (four-mode rendering), `dialog_restore` (scroll restore + learned styling), `selection_capture`, `extract_all_modes` (`a` shortcut in all four modes), `tts` (play chain), `learned_style`, `browser_menu`. Template loaded from the new `web/practice.html` path end-to-end
