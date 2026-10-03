"""Env-gated in-app self-test harness (development tooling).

Activated only when ``LSA_SELFTEST`` is set (points at a results JSON file).
Runs checks after the profile opens, writes results, then exits. Invisible to
normal users: without the env var, ``register()`` does nothing.

Every check records ``{"ok": bool, "detail": ...}``; a check must never raise
out of the runner — failures are captured with tracebacks.
"""

from __future__ import annotations

import json
import os
import traceback
from typing import Callable

RESULTS_ENV = "LSA_SELFTEST"
STARTUP_DELAY_MS = 1500
WATCHDOG_MS = 900_000
STEP_TIMEOUT_MS = 150_000
STARTUP_WATCHDOG_MS = 90_000

# Dev-run state: dialogs auto-dismissed before the profile opens (first-run
# language chooser etc.), recorded for evidence.
_dismissed: list[str] = []
_dismisser_active = False


def register() -> None:
    if not os.environ.get(RESULTS_ENV):
        return
    from aqt import gui_hooks

    gui_hooks.profile_did_open.append(_on_profile_open)
    _install_startup_dialog_dismiss()


def _install_startup_dialog_dismiss() -> None:
    """Close blocking first-run dialogs (e.g. the language chooser) until the
    profile opens; record their class names as evidence.

    Only QDialog instances are ever closed — never the main window — and
    profile-related dialogs are recorded but kept.
    """
    from aqt.qt import QDialog, QTimer

    global _dismisser_active
    _dismisser_active = True

    def tick() -> None:
        if not _dismisser_active:
            return
        try:
            from aqt.qt import QApplication

            for w in QApplication.topLevelWidgets():
                if not (isinstance(w, QDialog) and w.isVisible()):
                    continue
                cls = type(w).__name__
                key = f"{cls}:{w.windowTitle()}"
                if "profile" in cls.lower():
                    if key not in _dismissed:
                        _dismissed.append("SEEN-KEEP:" + key)
                    continue
                if key not in _dismissed:
                    _dismissed.append("CLOSED:" + key)
                w.close()
        except Exception:
            pass
        QTimer.singleShot(500, tick)

    def startup_timeout() -> None:
        path = os.environ.get(RESULTS_ENV)
        if not path or os.path.exists(path):
            return  # finished (or nothing to do)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    {"_meta": "STARTUP TIMEOUT: profile never opened",
                     "dialogs": _dismissed},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except OSError:
            pass
        os._exit(2)

    QTimer.singleShot(0, tick)
    QTimer.singleShot(STARTUP_WATCHDOG_MS, startup_timeout)


def _on_profile_open() -> None:
    from aqt.qt import QTimer
    from aqt import mw

    # First-run dialog dismissal is no longer needed once the profile is open
    # (selftest steps open their own dialogs intentionally).
    global _dismisser_active
    _dismisser_active = False
    QTimer.singleShot(STARTUP_DELAY_MS, lambda: _Runner(os.environ[RESULTS_ENV], mw).start())


class _Runner:
    """Sequential step queue: each step gets (mw, report, done)."""

    def __init__(self, results_path: str, mw) -> None:
        self.results_path = results_path
        self.mw = mw
        self.results: dict = {}
        self.steps: list[tuple[str, Callable]] = []
        self.current = "<startup>"
        self._finished = False

    # -- lifecycle -----------------------------------------------------
    def start(self) -> None:
        from aqt.qt import QTimer

        QTimer.singleShot(WATCHDOG_MS, self._force_finish)
        self._build_steps()
        self._run_next()

    def _run_next(self) -> None:
        if not self.steps:
            self._finish()
            return
        name, fn = self.steps.pop(0)
        self.current = name
        from aqt.qt import QTimer

        QTimer.singleShot(STEP_TIMEOUT_MS, lambda: self._step_timeout(name))
        try:
            fn(self.mw, self._report(name), lambda: self._step_done(name))
        except Exception:
            self.results[name] = {"ok": False, "detail": traceback.format_exc()}
            self._run_next()

    def _step_timeout(self, name: str) -> None:
        """Per-step backstop: a hung/failed async chain must not stall the suite."""
        if name != self.current:
            return  # already completed
        self.results[name] = {
            "ok": False,
            "detail": f"STEP TIMEOUT after {STEP_TIMEOUT_MS}ms",
        }
        self.current = "<between>"
        self._run_next()

    def _step_done(self, name: str) -> None:
        # Result already recorded by the step (ok/detail). Guard double-calls.
        if name != self.current:
            return
        self.current = "<between>"
        self._run_next()

    def _report(self, name: str) -> dict:
        report = {"ok": False, "detail": ""}
        self.results[name] = report
        return report

    def _finish(self) -> None:
        if self._finished:
            return
        self._finished = True
        self.results["_meta"] = {
            "last_step": self.current,
            "startup_dialogs": _dismissed,
        }
        self._write()
        if os.environ.get("LSA_SELFTEST_KEEP") == "1":
            # Keep Anki running so a human follow-up (e.g. the manual editor
            # spike) can happen in the same window; results are already on disk.
            return
        os._exit(0)

    def _force_finish(self) -> None:
        if self._finished:
            return
        self.results.setdefault(
            self.current, {"ok": False, "detail": "WATCHDOG TIMEOUT in this step"}
        )
        self._finish()

    def _write(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.results_path) or ".", exist_ok=True)
            with open(self.results_path, "w", encoding="utf-8") as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
        except OSError:
            pass

    # -- steps ---------------------------------------------------------
    def _build_steps(self) -> None:
        from . import selftest_checks, selftest_dialog_checks

        for name, fn in selftest_checks.CHECKS + selftest_dialog_checks.CHECKS_EXTRA:
            self.steps.append((name, fn))


def after_delay(ms: int, fn: Callable) -> None:
    from aqt.qt import QTimer

    QTimer.singleShot(ms, fn)
