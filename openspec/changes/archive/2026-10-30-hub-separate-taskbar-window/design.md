## Context

`HubWindow` is currently a `QDialog` subclass constructed with `parent=mw` (see proposal.md - Why). Qt parent-child ownership makes the Hub an owned top-level window on Windows: it has no taskbar button of its own, so a minimized Hub cannot be restored through normal platform affordances. The window already carries a `windowFlags` workaround adding `WindowMinimizeButtonHint` / `WindowMaximizeButtonHint` (a `Qt::Dialog` window on Windows gets neither caption button by default — same pattern as Anki's `aqt/models.py` dialog).

Anki's own Browser solves this by construction: `QMainWindow.__init__(self, None, Qt.WindowType.Window)` — no parent, explicit `Qt::Window` type bit. Verified against the Anki source shipped with the target Anki version (26.9.3 `browser.pyc` matches upstream `qt/aqt/browser/browser.py`).

The Hub reads `mw.col` in its bridge handlers and page renders; `mw` stays a plain attribute, not a Qt parent.

## Goals / Non-Goals

**Goals:**

- The Hub gets its own platform window entry (taskbar button on Windows); minimize + restore works like the Browser's.
- Losing the Qt parent does not leak the window: closing the profile or quitting Anki closes an open Hub.
- No behavior change to pages, bridge commands, singleton semantics, or the self-test contract (probes `web` / `selection` / `mode` / `close()`).

**Non-Goals:**

- Keeping the Hub visually above the main window (the Browser doesn't either; acceptable).
- macOS/Linux-specific window behavior beyond "works as a normal top-level window".
- Restoring window geometry across sessions.

## Decisions

**D1: `HubWindow` becomes a `QMainWindow` constructed Browser-style.**
`QMainWindow.__init__(self, None, Qt.WindowType.Window)`, then `self.mw = mw` as today; the `AnkiWebView` becomes the central widget via `setCentralWidget`. This is the exact Anki-endorsed pattern, so window flags, caption buttons, and taskbar behavior come from the platform defaults with zero flag hacks. Rationale over the alternatives:

- *QDialog with replaced type bits + parent=None*: same taskbar outcome but semantically "dialog pretending to be a window"; `QDialog` adds accept/reject/Esc-close semantics the Hub doesn't use and may want to avoid (Esc while practicing should not close the Hub).
- *ctypes `WS_EX_APPWINDOW` while keeping parent*: preserves always-on-top and auto-destroy, but is a Windows-only, Qt-version-fragile hack; rejected.
- *Keep QDialog, only remove minimize*: works against the stated goal (Browser-like separate window).

**D2: Drop the min/max `windowFlags` workaround.**
`QMainWindow` on Windows gets minimize/maximize caption buttons natively; the flags hack (and its comment referencing `aqt/models.py`) is deleted with the `QDialog` base. Requirement "Minimize and maximize controls" stays satisfied — by construction now.

**D3: Explicit profile-close lifecycle replaces Qt parent-child destruction.**
`register()` adds `gui_hooks.profile_will_close` → close the singleton Hub (guarded by try/except + the existing `_hub is not None` check). `closeEvent` already clears the `_hub` global, so no other cleanup path changes. Rationale: `profile_will_close` is the hook Anki's own `main.pyc` uses; it fires before `mw.col` goes away, so a Hub closed there never touches a dead collection. Alternatives: `aqt.dialogs` registry (Anki-managed dialog lifecycle) — heavier and designed for Anki's own dialogs; `app_will_exit` — too late / not guaranteed on profile switch.

**D4: `open_hub(parent=None, ...)` keeps its signature; the `parent` argument becomes unused.**
Callers (`_on_menu_triggered`, `practice_dialog.open_dialog`, self-test) pass it positionally. Keeping the parameter avoids breaking the self-test's `open_dialog(parent=None, note_id, mode)` contract in this change; removing it is a follow-up cleanup, not this scope.

## Risks / Trade-offs

- [Hub no longer stays above the main window] → Accepted; identical to Browser behavior. The Tools-menu raise path (`_raise`) already restores it.
- [`profile_will_close` hook misbehaves across Anki versions] → It is present in the target 26.9.3 and long-stable in Anki; registration wrapped in try/except so a missing hook degrades to a no-op, not an add-on failure.
- [Self-test startup dialog dismisser] → It closes only visible `QDialog` instances; a `QMainWindow` Hub is immune. Verify the dismisser never needed to close the Hub (it didn't — the Hub can't exist during startup).
- [`tests/test_hub.py` stub breaks] → The stub provides `qt.QDialog`; it must provide `qt.QMainWindow` instead. Trivial, called out in tasks.
- [Escape key] → `QDialog` closes on Esc by default; `QMainWindow` does not. The Hub never wanted Esc-to-close (practice pages hold selections), so this is a mild improvement, but note it in case any user relied on it.

## Open Questions

None blocking. Whether to later drop the now-unused `parent` parameter from `open_hub` / `open_dialog` is a cleanup decision that does not affect this change's specs or task list.
