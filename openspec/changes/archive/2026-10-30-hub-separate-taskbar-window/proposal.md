## Why

On Windows the Hub window is a `QDialog` parented to Anki's main window, so it is an owned window with no taskbar button of its own; once minimized there is no normal way to bring it back — the only recovery path is re-triggering the Tools menu. Anki's own Browser avoids exactly this by being a parentless `QMainWindow` (`QMainWindow.__init__(self, None, Qt.WindowType.Window)`); the Hub should follow the same established pattern.

## What Changes

- `HubWindow` changes base class from `QDialog` to `QMainWindow`, constructed the same way as Anki's Browser: no parent, explicit `Qt.WindowType.Window` flag; the `AnkiWebView` becomes the window's central widget.
- The `windowFlags` workaround that added minimize/maximize caption buttons to a `Qt::Dialog` window on Windows is removed — `QMainWindow` exposes both natively.
- The Hub is no longer owned by the main window, so its lifecycle is taken over explicitly: closing the Anki profile closes the Hub window (previously guaranteed by Qt parent-child destruction).
- A minimized Hub becomes restorable from its own taskbar/button entry on Windows, satisfying the existing window-management requirement's recovery scenario as intended.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `practice-hub`: The Hub window becomes an independent top-level window — it has its own taskbar/button entry instead of sharing the main window's, and closing the Anki profile closes the Hub window.
- `practice-dialog`: The window-management requirement's minimize/restore scenario gains the concrete guarantee that the minimized Hub is restorable via the Hub's own taskbar/button entry (replacing the platform-agnostic "taskbar/button or equivalent" hedge).

## Impact

- `language_study_anki/hub.py` — `HubWindow` class (base class, construction, layout), `open_hub()` (no parent argument), `register()` (profile-close hook registration).
- `tests/test_hub.py` — the minimal `aqt.qt` stub must provide `QMainWindow` instead of `QDialog`.
- `language_study_anki/selftest.py` — the startup dialog dismisser only closes `QDialog` instances; the Hub becomes `QMainWindow` and is therefore unaffected (verify, no change expected).
- `language_study_anki/selftest_dialog_checks.py` — probes the Hub via `web` / `selection` / `mode` / `close()`; these survive the base-class change untouched (verify).
- No changes to note types, storage, web templates, bridge commands, or the extract flow.
