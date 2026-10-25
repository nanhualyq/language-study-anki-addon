## Why

`practice_dialog.py` is 364 lines, of which ~216 (60%) are the `_HTML` template string — the only module in the package over 206 lines. Inside a raw Python string the HTML/CSS/JS gets no editor highlighting, linting, or formatting, which makes maintaining and locating UI code (styles, mode rules, selection logic) slower than it needs to be.

## What Changes

- Move the `_HTML` template verbatim out of `practice_dialog.py` into a new resource file `language_study_anki/web/practice.html`.
- `practice_dialog.py` reads the file once (path resolved relative to `__file__`), caches the string, and continues substituting `__MODE__` / `__LSA_DATA__` exactly as before.
- Add cross-referencing comments on both sides documenting the Python↔HTML contract: placeholders (`__MODE__`, `__LSA_DATA__`), bridge commands (`lsa:sel:`, `lsa:extract`, `lsa:play:<n>`), and the `window.markLearnedUpTo(n)` callback.
- No behavior change: rendered DOM, bridge protocol, and dialog lifecycle are byte-for-byte identical.

## Capabilities

### New Capabilities

(none — pure refactor)

### Modified Capabilities

(none — rendering behavior in `openspec/specs/practice-dialog/` is unchanged)

This change declares no spec deltas and sets `skip_specs: true`: specs describe behavior, and the practice-dialog behavior (rendering, toolbar, scroll restore, reveal controls, selection capture) is untouched.

## Impact

- `language_study_anki/practice_dialog.py` — template removed; small read-once loader added.
- `language_study_anki/web/practice.html` — new file (moved template).
- Deployment unaffected: `tools/deploy-prod.sh` copies the package directory wholesale (excludes only `__pycache__`/`*.pyc`/`meta.json`), and `.ankiaddon` packaging includes the new file.
- No test impact: `_HTML` is referenced nowhere in `tests/`; `selftest_dialog_checks.py` drives the real dialog in-app and does not depend on the template's location.
- No resource-loading risk: the file is read by Python and passed to `setHtml()` as a string, so QWebEngine never resolves local paths (no baseUrl concerns).
