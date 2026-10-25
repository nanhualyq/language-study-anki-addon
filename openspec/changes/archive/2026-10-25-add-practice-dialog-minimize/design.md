## Context

`PracticeDialog` subclasses `QDialog` with default window flags. On Windows, a `Qt::Dialog`-typed window gets `WS_SYSMENU` and `WS_THICKFRAME` but neither `WS_MINIMIZEBOX` nor `WS_MAXIMIZEBOX` — confirmed live against the running instance:

```
Practice: Listening — Homeland.S08E12
  style=0x96CC0000
  WS_MINIMIZEBOX=False  WS_MAXIMIZEBOX=False  WS_SYSMENU=True  WS_THICKFRAME=True
  exstyle=0x100 (WS_EX_WINDOWEDGE; no WS_EX_APPWINDOW)
  owner = Browse window
```

The dialog is opened by `open_dialog()` in `language_study_anki/practice_dialog.py`, which keeps it in the `_open` registry keyed by `(note_id, mode)`, and it is parented to the Browser window (owned window). See proposal.md for motivation.

Constraints shaping the approach:

- The dialog must remain a `QDialog`: `selftest.py` deliberately closes only `QDialog` instances (never the main window) and `selftest_dialog_checks.py` performs `isinstance`-based checks against `open_dialog()` results.
- The spec's existing behavior (extract-only progress, no writes on close, scroll restore) must be untouched — window management actions are orthogonal to it.

## Goals / Non-Goals

**Goals:**

- Working minimize and maximize controls on the practice dialog caption, restoring with all in-dialog state intact.
- Minimum possible diff inside `PracticeDialog.__init__`.

**Non-Goals:**

- Changing the window class (no `QMainWindow`, no plain `QWidget`, no embedding into the main window or Browser tabs).
- Changing modality, ownership, the `_open` registry, or close behavior.
- Tray icon / minimize-to-tray behavior.
- Touching `web/practice.html` or the selftest suite.

## Decisions

**D1: OR the button hints onto the existing `QDialog` flags.**

```python
self.setWindowFlags(
    self.windowFlags()
    | Qt.WindowType.WindowMinimizeButtonHint
    | Qt.WindowType.WindowMaximizeButtonHint
)
```

Rationale: it is the smallest change that yields the required observable behavior, and it is the exact pattern Anki itself uses — `aqt/models.py` (Manage Note Types) applies `windowFlags() | WindowMaximizeButtonHint | WindowMinimizeButtonHint` to its own `QDialog`. Precedent inside the host application means no surprising platform behavior.

*Alternatives considered:*

- **B: `QDialog` with `Qt.WindowType.Window` type** — turns it into a normal window. Keeps `isinstance(QDialog)` working, but changes window semantics (taskbar/ownership behavior) more than needed for two caption buttons.
- **C: plain `QWidget` + `Qt.Window`** — breaks `selftest.py`'s QDialog-only safety guard and `selftest_dialog_checks.py` isinstance checks; guard rewrite is out of scope.
- **D: `QMainWindow`** — what the Browser uses, but brings menu/toolbar/status-bar machinery the dialog does not need; same selftest breakage as C.
- **E: embed in main window / Browser tab** — architectural rewrite; "minimize" becomes meaningless; spec's per-article-dialog positioning would need a full rewrite.

**D2: Set flags in `__init__`, before `show()` is called by `open_dialog()`.** Flags applied before the native window is shown avoid a visible re-styling flash and avoid `setWindowFlags()` re-creating an already-shown window (which would drop its state).

## Risks / Trade-offs

- [The dialog is an owned window (owner = Browse) without `WS_EX_APPWINDOW`, so Windows may not give it an independent taskbar button — a minimized dialog might have no obvious restore affordance] → This is the gating verification task: after applying D1, minimize the dialog and confirm it can be restored (expected: clicking the owner's taskbar button or the dialog's own taskbar entry restores it). If restore turns out to be impossible, fall back to decision B (`Qt.WindowType.Window`), which detaches the window type from dialog semantics and typically yields its own taskbar entry.
- [Minimizing the dialog while the Browser (owner) is minimized cascades] → Standard owned-window semantics; acceptable, no mitigation needed.
- [`setWindowFlags` after `show()` would hide/re-create the window] → D2 orders construction so flags are set pre-show; noted in tasks.
- [Maximize may stretch the web view in unexpected ways at extreme aspect ratios] → The layout is a single `QVBoxLayout` containing `AnkiWebView`, which reflows; verified by the maximize/restore scenario, no pre-emptive work.

## Migration Plan

Not applicable — additive caption-button change, no data or schema migration. Rollback = remove the two flag lines.

## Open Questions

- Whether the minimized dialog gets its own taskbar entry (owner is the Browse window) — **must be answered by measurement in the tasks**, not guessed; it determines whether D1 suffices or the fallback to decision B is needed. This does not change the specs (the spec already requires restorability) but it does gate task completion.
