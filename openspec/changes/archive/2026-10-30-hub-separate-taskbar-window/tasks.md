## 1. Test stub groundwork

- [x] 1.1 Update `tests/test_hub.py`'s `_stub_aqt_qt()` to provide `qt.QMainWindow` (plain class) in place of the `qt.QDialog` stub, keeping the `Qt.WindowType` hints stub, and verify `python -m unittest tests.test_hub` still passes

## 2. HubWindow base-class change (design D1/D2)

- [x] 2.1 In `language_study_anki/hub.py`, change `HubWindow` to subclass `QMainWindow`: construct with `QMainWindow.__init__(self, None, Qt.WindowType.Window)`, keep `self.mw = mw`, add the `AnkiWebView` via `setCentralWidget` instead of `QVBoxLayout`; update the import line; verify `python -m unittest discover tests` passes
- [x] 2.2 Delete the `setWindowFlags(... MinimizeButtonHint ... MaximizeButtonHint)` block and its `aqt/models.py` comment (QMainWindow has both natively); verify no remaining references to those flags in `hub.py`
- [x] 2.3 Update the module docstring's decision references (D1 "single QDialog window") to describe the QMainWindow Browser-style window; verify the docstring matches the new code

## 3. Explicit lifecycle (design D3)

- [x] 3.1 In `register()`, subscribe `gui_hooks.profile_will_close` to close the singleton Hub (`_hub.close()` when non-null, try/except-wrapped, registered once — follow the existing addon-reload guard pattern); verify the hook registration is guarded against duplicate registration like the QAction is
- [x] 3.2 Verify `closeEvent` still clears the `_hub` global so the closed-then-reopened singleton path works (no code change expected — confirm by reading)

## 4. Self-test and integration verification

- [x] 4.1 Run the in-Anki self-test and confirm `check_hub_list` and the practice-dialog checks still pass with the QMainWindow Hub (they probe `web` / `selection` / `mode` / `close()`, which the new base class preserves)
- [x] 4.2 Confirm the startup dialog dismisser in `selftest.py` (QDialog-only) does not interact with the Hub window (expected: no change needed)
- [x] 4.3 Manual verification in Anki on Windows: open the Hub from the Tools menu, minimize it, and confirm it is restorable from its own taskbar button; open practice, minimize, restore, and confirm scroll/revealed-lines/selection are unchanged; close the profile with the Hub open and confirm the Hub closes without error and no progress field is written
