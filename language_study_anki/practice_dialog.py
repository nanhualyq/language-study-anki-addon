"""Practice dialog: one QWebEngine window, four skill modes.

Specs: practice-dialog (entry, rendering, scroll restore, selection capture).
Decision D4: mode is a rendering flag; Python owns progress I/O, TTS requests
and extraction. No progress writes happen here — scrolling and dialog close
never write (decision D8): the dialog only READS the mode's progress field.
"""

from __future__ import annotations

import json
import os
import traceback

from aqt.qt import QDialog, Qt, QVBoxLayout

from . import tts
from .progress import get_progress, progress_field
from .provisioning import ARTICLE_NOTE_TYPE
from .suspension import ensure_note_suspended
from .storage import field_to_lines

MODES = ("reading", "speaking", "listening", "writing")
MODE_LABELS = {
    "reading": "Practice: Reading",
    "speaking": "Practice: Speaking",
    "listening": "Practice: Listening",
    "writing": "Practice: Writing",
}

# Set/kept by open(); prevents GC and duplicate windows per note+mode.
_open: dict[tuple[int, str], "PracticeDialog"] = {}

# The practice-dialog UI template. Read once at import (D1 in change
# extract-practice-html-template): a missing file is a deploy error and
# should fail loudly at Anki startup, not on first click.
# CONTRACT with web/practice.html (keep both ends in sync):
#   Placeholders replaced before setHtml: __MODE__, __LSA_DATA__
#   Bridge commands (JS -> Python via pycmd): lsa:sel:<json|null>,
#     lsa:extract, lsa:play:<n>
#   Callback (Python -> JS): window.markLearnedUpTo(n)
_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "web", "practice.html")
try:
    with open(_TEMPLATE_PATH, encoding="utf-8") as _f:
        _HTML = _f.read()
except FileNotFoundError as e:
    raise FileNotFoundError(
        f"language_study_anki: practice template not found: {_TEMPLATE_PATH}"
    ) from e


def open_dialog(parent, note_id: int, mode: str) -> "PracticeDialog":
    assert mode in MODES, mode
    key = (note_id, mode)
    old = _open.get(key)
    if old is not None:
        try:
            old.close()
        except Exception:
            pass
    from aqt import mw

    dlg = PracticeDialog(parent, mw, note_id, mode)
    _open[key] = dlg
    dlg.show()
    dlg.raise_()
    dlg.activateWindow()
    return dlg


class PracticeDialog(QDialog):
    def __init__(self, parent, mw, note_id: int, mode: str) -> None:
        super().__init__(parent)
        self.mw = mw
        self.note_id = note_id
        self.mode = mode
        self.selection: dict | None = None
        self._lines: list[str] = []
        self._translations: list[str] = []

        note = mw.col.get_note(note_id)
        if note.note_type()["name"] != ARTICLE_NOTE_TYPE:
            raise ValueError("not an article note")
        # D2 enforcement point: repair cards regenerated unsuspended by
        # template edits, at the moment the system next touches the article.
        ensure_note_suspended(note)

        self._article = note
        self._lines = field_to_lines(note["Content"])
        self._translations = field_to_lines(note["Translation"])
        progress = get_progress(note, mode)

        self.setWindowTitle(f"{MODE_LABELS[mode]} — {note['Title']}")
        # Qt::Dialog windows get no min/max caption buttons on Windows
        # (WS_MINIMIZEBOX/WS_MAXIMIZEBOX absent). Same pattern as Anki's own
        # aqt/models.py dialog. Set before show() (D2 in design.md).
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )
        self.resize(920, 720)
        layout = QVBoxLayout(self)

        from aqt.webview import AnkiWebView

        self.web = AnkiWebView()
        try:
            self.web.set_bridge_command(self._on_bridge, self)
        except (AttributeError, TypeError):
            self.web.onBridgeCmd = self._on_bridge
        layout.addWidget(self.web)

        data = {
            "mode": mode,
            "title": note["Title"],
            "lines": self._lines,
            "translations": self._translations,
            "progress": progress,
            "progressField": progress_field(mode),
        }
        html = _HTML.replace("__MODE__", mode).replace(
            "__LSA_DATA__", json.dumps(data, ensure_ascii=False)
        )
        try:
            self.web.setHtml(html)
        except TypeError:
            self.web.setHtml(html, None)

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        # Decision D8: no progress writes on close.
        _open.pop((self.note_id, self.mode), None)
        super().closeEvent(event)

    # -- bridge --------------------------------------------------------
    # JS side lives in web/practice.html; commands must match the contract
    # comment at _TEMPLATE_PATH above (lsa:sel:, lsa:extract, lsa:play:<n>).
    def _on_bridge(self, cmd: str) -> None:
        log = getattr(self, "bridge_log", None)
        if log is None:
            log = self.bridge_log = []
        log.append(cmd[:120])
        if len(log) > 8:
            del log[: len(log) - 8]
        try:
            if cmd.startswith("lsa:sel:"):
                payload = cmd[len("lsa:sel:"):]
                self.selection = None if payload in ("null", "-") else json.loads(payload)
            elif cmd == "lsa:extract":
                from . import extract

                extract.run_extract(self)
            elif cmd.startswith("lsa:play:"):
                idx = int(cmd.split(":", 2)[2])
                self._play_line(idx)
        except Exception:
            print("language_study_anki: bridge error:\n" + traceback.format_exc())

    def _play_line(self, line_no: int) -> None:
        if not 1 <= line_no <= len(self._lines):
            return
        try:
            tts.speak(self._lines[line_no - 1])
        except Exception as e:
            # Spec: failure must not crash the dialog; non-blocking feedback.
            try:
                from aqt.qt import QApplication
                from aqt.utils import tooltip

                tooltip(f"TTS error: {e}")
                QApplication.beep()
            except Exception:
                pass
