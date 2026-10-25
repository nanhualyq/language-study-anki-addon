## Context

`practice_dialog.py` ends with the `_HTML` raw string (template for all four skill modes), rendered via `setHtml()` after `__MODE__` / `__LSA_DATA__` substitution. See proposal.md — Why. Facts verified during exploration:

- Nothing in `tests/` or `selftest_*` references `_HTML`; the self-test drives the real dialog in-app.
- `tools/deploy-prod.sh` copies `language_study_anki/` wholesale (excludes `__pycache__`, `*.pyc`, `meta.json`), so a new `web/` subdirectory ships with no script changes.
- `setHtml()` receives a full string; QWebEngine never resolves local file paths, so no baseUrl/resource-loading constraints apply.

## Goals / Non-Goals

**Goals:**

- Template lives in `web/practice.html` where editors provide full HTML/CSS/JS highlighting, linting, and formatting.
- Python/HTML contract (placeholders, bridge commands, callbacks) explicitly documented at both ends.
- Byte-identical rendered output; zero behavior change.

**Non-Goals:**

- No dev harness / browser-preview shim (`pycmd` mock, mock data) — deferred; add later only if UI iteration frequency justifies it.
- No template engine, no CSS/JS asset splitting, no visual changes of any kind.
- No changes to the bridge protocol or data payload shape.

## Decisions

**D1 — Read the template once at module load, cache the string.**
Module-level `_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "web", "practice.html")`, read into `_HTML` at import. Dialog construction (and the `.replace()` pipeline) is unchanged.
*Alternative considered:* lazy read on first dialog open — keeps startup untouched if the file is missing, but adds a mutable cache state for no practical gain; a missing file is a deploy error and should fail loudly at import (the browser-menu import chain surfaces it immediately at Anki startup, which is easier to diagnose than a failure on first click).

**D2 — Verbatim move; keep string `.replace()` substitution.**
The template moves unchanged (`__MODE__`, `__LSA_DATA__` placeholders stay). No templating library.
*Rationale:* substitution is two replacements on a known string; a library would add a dependency and reformatting noise to a diff whose whole point is provable equivalence.

**D3 — Document the contract in comments at both ends.**
Top of `web/practice.html`: produced/consumed by `practice_dialog.py`, lists placeholders and bridge commands, warns that edits must keep the contract. In `practice_dialog.py` next to the loader and in `_on_bridge`: pointer to the template file and the reverse contract list (placeholders, `lsa:sel:` / `lsa:extract` / `lsa:play:<n>`, `window.markLearnedUpTo(n)`).
*Rationale:* the contract was previously visible within one file; cross-references are the mitigation for the split.

**D4 — HTML syntax comment conventions unchanged.**
The template keeps its existing rationale comments (e.g. learned-row background, twisty reveal) — they are the institutional memory for spec decisions (opacity, single reveal mechanism) and move with the code.

## Risks / Trade-offs

- [Template file missing at runtime (partial deploy)] → Module import raises `FileNotFoundError` with the resolved path in the message; loud and early (D1).
- [One side of the contract edited without the other] → Cross-referencing comments (D3); the in-app self-test (`selftest_dialog_checks.py`) exercises the real dialog end-to-end and would catch protocol breaks.
- [Deploy/packaging drops non-`.py` files] → Verified: deploy script copies the directory wholesale; `.ankiaddon` zips include resources. No action needed.

## Migration Plan

Single commit: add `web/practice.html`, delete the `_HTML` string, add loader + comments. Rollback = revert the commit. No data, note-type, or on-disk-format changes; no user-visible migration.

## Open Questions

None.
