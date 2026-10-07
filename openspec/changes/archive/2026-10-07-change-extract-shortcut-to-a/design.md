## Context

The practice dialog (`language_study_anki/practice_dialog.py`) injects HTML+JS into Anki's webview. A `document.addEventListener('keydown', …)` handler currently listens for `Ctrl+E` (or `Meta+E`) and issues `pycmd('lsa:extract')`, which Python routes to `run_extract` in `extract.py`. A hint line in the same HTML tells the user to "press Ctrl+E to extract", `README.md` documents the chord, and `selftest_dialog_checks.py` simulates the chorded keydown to verify the extract flow end-to-end. The dialog HTML contains no editable fields (no inputs, textareas, or contenteditable regions), so a bare-key shortcut cannot collide with typing.

See proposal.md for motivation; specs/practice-extract/spec.md for the required behavior.

## Goals / Non-Goals

**Goals:**
- Trigger extraction on the bare `a` key only (no Ctrl/Meta/Alt/Shift).
- Fully retire `Ctrl+E` as an extract trigger (no dual binding).
- Keep all hint text, docs, and self-tests consistent with the new key.

**Non-Goals:**
- Making the shortcut configurable (no settings UI).
- Changing selection capture, note building, progress, or provisioning behavior.
- Supporting other single-letter shortcuts.

## Decisions

1. **Replace, don't add.** `Ctrl+E` stops triggering extraction entirely. Rationale: the user asked to *change* the shortcut ("换个简单的 a"); keeping both doubles the surface to document and test and leaves two ways to do one thing. Alternative considered: keep `Ctrl+E` as a hidden alias — rejected as unrequested complexity.

2. **Modifier check, not just `e.key === 'a'`.** The handler requires `e.key` to be `a`/`A` **and** none of `ctrlKey`, `metaKey`, `altKey`, `shiftKey`. Rationale: without this, `Ctrl+A` (select-all) would open the Add dialog on an existing selection — an easy misfire. The spec's "Old chord no longer extracts" scenario pins this. Alternative: allow `Shift+A` — rejected; capital letters are usually incidental.

3. **Trigger regardless of focus target.** The listener stays on `document` with no editable-field guard, matching today's behavior. Rationale: the dialog has no editable elements, so a guard would be dead code; if inputs are ever added, that is the moment to add an `isContentEditable`/tagName check.

4. **Single source of truth for the key is code, mirrored in three places.** The literal lives in the JS handler; the hint text, `README.md`, `extract.py` docstring, and `selftest_dialog_checks.py` event payload are updated in the same change. No constant is threaded through (JS string + HTML text + Python docstring don't share literals today) — acceptable for a one-line key.

## Risks / Trade-offs

- [Bare `a` may fire when the user didn't intend extraction (e.g., rapid typing)] → Mitigated: the dialog is read-only, and the no-selection path is a no-op, so at worst an unwanted Add dialog opens and the user cancels; same blast radius as today's `Ctrl+E`.
- [Muscle memory / documented `Ctrl+E` in README and external notes] → Hint line updated in-dialog (primary discovery surface); README updated; spec scenario documents that the old chord is inert.
- [Self-test hard-codes the key payload] → `selftest_dialog_checks.py` dispatches `{key:'a'}` with no modifier flags; running the self-test after the change verifies wiring.

## Migration Plan

Single-commit, in-repo change; no config or data migration. Rollback = revert the commit (behavior returns to `Ctrl+E`).

## Open Questions

None.
