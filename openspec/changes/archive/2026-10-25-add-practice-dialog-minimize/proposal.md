## Why

The practice dialog (`PracticeDialog`, a plain `QDialog`) cannot be minimized: Windows gives `Qt::Dialog`-typed windows no minimize/maximize caption buttons (measured live: `WS_MINIMIZEBOX=False`, `WS_MAXIMIZEBOX=False` while `WS_THICKFRAME=True`). A user practicing with an article stuck in front of Anki has no way to tuck it away without closing it — and closing throws away the on-screen scroll position (progress is extract-only by design). Anki's own dialogs that need min/max (e.g. Manage Note Types) solve this by explicitly OR-ing the button hints onto their `QDialog`; this change applies the same established pattern.

## What Changes

- `PracticeDialog` sets `Qt.WindowType.WindowMinimizeButtonHint` and `Qt.WindowType.WindowMaximizeButtonHint` on its window flags at construction, so the caption shows working minimize and maximize buttons.
- The dialog remains a `QDialog` — no change to window type, modality, ownership, lifecycle, or the `_open` registry.
- Verify (and record) the recovery behavior of a minimized dialog: the window is an owned window without `WS_EX_APPWINDOW`, so its independent taskbar-button presence must be confirmed before the change is considered done.

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `practice-dialog`: add a window-management requirement — the practice dialog's caption SHALL expose minimize and maximize controls that work, and a minimized dialog SHALL be restorable.

## Impact

- Code: `language_study_anki/practice_dialog.py` (`PracticeDialog.__init__`, ~2 lines).
- Tests/selftest: none required to change — the dialog stays a `QDialog`, so `selftest.py`'s "only close QDialog instances" guard and `selftest_dialog_checks.py`'s `isinstance` checks keep working as-is.
- Specs: delta in `openspec/changes/add-practice-dialog-minimize/specs/practice-dialog/spec.md`.
- No dependency, packaging, or template (`web/practice.html`) changes.
