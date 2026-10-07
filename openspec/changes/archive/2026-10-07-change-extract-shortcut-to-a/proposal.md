## Why

Extracting the current selection is the core interaction of the practice dialog, but `Ctrl+E` is a two-key chord that is awkward to hit repeatedly while reading. The user wants a single, simpler key: `a`.

## What Changes

- **BREAKING**: The extract shortcut in the practice dialog changes from `Ctrl+E` to the bare `a` key. `Ctrl+E` no longer triggers extraction (assumption: full replacement, not an additional binding — see design.md).
- The in-dialog hint text (`select text & press Ctrl+E to extract`) is updated to reference `a`.
- Docs (`README.md`) and code comments that document `Ctrl+E` as the extract shortcut are updated.
- Self-test dialog checks fire the new key instead of `Ctrl+E`.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `openspec/specs/practice-extract/spec.md`: The "Keyboard shortcut triggers extraction" requirement changes the trigger from `Ctrl+E` to the bare `a` key; scenarios updated accordingly.

## Impact

- `language_study_anki/practice_dialog.py` — the `keydown` listener in the injected HTML and the hint text.
- `language_study_anki/extract.py` — docstring referencing the `Ctrl+E` handler.
- `language_study_anki/selftest_dialog_checks.py` — simulated keydown event used in the extract self-test.
- `README.md` — user-facing feature description.
- No AnkiConnect, note-building, progress, or provisioning behavior changes.
