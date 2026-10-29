"""Article-list Hub: one window, two pages (list <-> practice).

Specs: practice-hub (Tools-menu entry, singleton, list page, navigation,
return-to-list) and practice-dialog (the practice page rendered inside this
window; the old Browser context-menu entry is gone).

Decisions (design.md): D1 single QDialog window; D2 page swap by setHtml in
one AnkiWebView; D3 bridge navigation commands lsa:open / lsa:back;
D4 practice-page state lives here so extract.py and the self-test keep
reading the same attributes they read off the old PracticeDialog;
D7 Tools-menu registration with a no-profile guard.

CONTRACT with web/list.html and web/practice.html (keep both ends in sync):
  Placeholders replaced before setHtml:
    list.html     __LSA_DATA__    JSON {rows:[{id,title,pcts:{...}}]}
    practice.html __MODE__, __LSA_DATA__  (practice payload, unchanged)
  Bridge commands (JS -> Python via pycmd):
    lsa:open:<note_id>:<mode>  list page -> enter practice (list page only)
    lsa:back                   practice page -> return to the list
    lsa:sel:<json|null>        practice: live text-selection update
    lsa:extract                practice: run extraction on the selection
    lsa:play:<n>               practice: TTS-play line n (1-based)
  Callback (Python -> JS): window.markLearnedUpTo(n) (practice page)
"""

from __future__ import annotations

import json
import os
import traceback

from aqt.qt import QDialog, Qt, QVBoxLayout

from . import tts
from .practice_dialog import MODE_LABELS, MODES
from .progress import get_progress, progress_field
from .provisioning import ARTICLE_NOTE_TYPE
from .suspension import ensure_note_suspended
from .storage import field_to_lines

LIST_TITLE = "Language Study"
MENU_LABEL = "Language Study: Article List"
_MENU_OBJECT_NAME = "lsa_article_list"

_WEB_DIR = os.path.join(os.path.dirname(__file__), "web")


def _read_template(name: str) -> str:
    """Read an HTML template once at import — a missing file is a deploy
    error and should fail loudly at Anki startup, not on first click."""
    path = os.path.join(_WEB_DIR, name)
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"language_study_anki: template not found: {path}"
        ) from e


_PRACTICE_HTML = _read_template("practice.html")
_LIST_HTML = _read_template("list.html")

# Singleton window: one Hub at a time (spec: practice-hub → Tools-menu
# entry; repeated menu choices raise this window instead of opening a
# second one). Cleared by HubWindow.closeEvent.
_hub: "HubWindow | None" = None


# ------------------------------------------------------------ list data


def _progress_percent(note, skill: str) -> int:
    """Integer percent (0-100, half-up) of the note's Content covered by
    the skill's stored progress line. 0% for empty Content or no progress;
    100% when progress reaches/exceeds the line count.

    (Same rules the removed Browser context-menu labels used — now on each
    list row; spec: practice-hub → Article list page.)
    """
    try:
        total = len(field_to_lines(note["Content"]))
    except Exception:
        return 0
    if total <= 0:
        return 0
    line = get_progress(note, skill)
    if line <= 0:
        return 0
    if line >= total:
        return 100
    return int(line * 100.0 / total + 0.5)


def list_payload(col) -> dict:
    """List-page data: one row per Article note, most recently created
    first.

    Anki note ids are generated monotonically from the clock, so descending
    id = newest first (spec: practice-hub → Article list page).
    """
    try:
        note_ids = col.find_notes(f'"note:{ARTICLE_NOTE_TYPE}"')
    except Exception:
        note_ids = []
    rows = []
    for nid in sorted(note_ids, reverse=True):
        try:
            note = col.get_note(nid)
        except Exception:
            continue
        try:
            title = note["Title"] or ""
        except KeyError:
            title = ""
        # Cover is user-maintained and may be absent on an adopted or
        # freshly provisioned note, so a missing field yields "" rather
        # than raising (spec: practice-hub → Article list page).
        try:
            cover = note["Cover"] or ""
        except KeyError:
            cover = ""
        rows.append(
            {
                "id": int(nid),
                "title": title,
                "cover": cover,
                "pcts": {m: _progress_percent(note, m) for m in MODES},
            }
        )
    return {"rows": rows}


def list_html(payload: dict) -> str:
    """list.html with the payload injected (contract placeholder)."""
    return _LIST_HTML.replace(
        "__LSA_DATA__", json.dumps(payload, ensure_ascii=False)
    )


# -------------------------------------------------------- practice page


class PracticePage:
    """Practice-page state for one article+mode inside the Hub.

    Owns the fields extract.py reads off the dialog (note, lines,
    translations, selection); the webview itself belongs to HubWindow.
    Created fresh on every entry into practice — returning to the list
    discards the practice DOM (design non-goal), and re-entering re-renders
    from the note's fields.
    """

    def __init__(self, note, mode: str) -> None:
        self.note = note
        self.mode = mode
        self.selection: dict | None = None
        self.lines = field_to_lines(note["Content"])
        self.translations = field_to_lines(note["Translation"])

    def payload(self) -> dict:
        return {
            "mode": self.mode,
            "title": self.note["Title"],
            "lines": self.lines,
            "translations": self.translations,
            "progress": get_progress(self.note, self.mode),
            "progressField": progress_field(self.mode),
        }

    def play_line(self, line_no: int) -> None:
        """TTS-play line n (1-based); failure is non-blocking feedback."""
        if not 1 <= line_no <= len(self.lines):
            return
        try:
            tts.speak(self.lines[line_no - 1])
        except Exception as e:
            try:
                from aqt.qt import QApplication
                from aqt.utils import tooltip

                tooltip(f"TTS error: {e}")
                QApplication.beep()
            except Exception:
                pass


class HubWindow(QDialog):
    """Single window with two pages: article list <-> practice
    (spec: practice-hub). One AnkiWebView; pages swap via setHtml."""

    def __init__(
        self,
        parent,
        mw,
        note_id: int | None = None,
        mode: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.mw = mw
        self._page = "list"
        self._practice: PracticePage | None = None
        self.bridge_log: list[str] = []
        self.extract_log: list[str] = []

        self.setWindowTitle(LIST_TITLE)
        # Qt::Dialog windows get no min/max caption buttons on Windows
        # (WS_MINIMIZEBOX/WS_MAXIMIZEBOX absent). Same pattern as Anki's own
        # aqt/models.py dialog. Set before show() (practice-dialog spec:
        # Minimize and maximize controls).
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

        if note_id is not None:
            self.show_practice(note_id, mode)
        else:
            self.show_list()

    # -- pages --------------------------------------------------------

    def _set_html(self, html: str) -> None:
        try:
            self.web.setHtml(html)
        except TypeError:
            self.web.setHtml(html, None)

    def show_list(self) -> None:
        """Render the article list page from a fresh collection read, so
        percentages reflect extracts made during practice (spec:
        practice-hub → Return to list)."""
        self._page = "list"
        if self._practice is not None:
            # Selection is practice-page state; clear it on return. The
            # PracticePage itself is kept only so an extract still finishing
            # its dictionary lookup can complete after the user navigated
            # back (it reads the note/lines off this object).
            self._practice.selection = None
        self.setWindowTitle(LIST_TITLE)
        self._set_html(list_html(list_payload(self.mw.col)))

    def show_practice(self, note_id: int, mode: str | None) -> None:
        """Render the practice page for one article+mode (spec:
        practice-dialog). Also the D2 enforcement point: repair cards
        regenerated unsuspended by template edits, at the moment the
        system next touches the article."""
        assert mode in MODES, mode
        note = self.mw.col.get_note(note_id)
        if note.note_type()["name"] != ARTICLE_NOTE_TYPE:
            raise ValueError("not an article note")
        ensure_note_suspended(note)

        self._practice = PracticePage(note, mode)
        self._page = "practice"
        # Fresh practice session = fresh diagnostics (old code got this for
        # free because every open_dialog created a new window).
        self.bridge_log = []
        self.extract_log = []
        self.setWindowTitle(f"{MODE_LABELS[mode]} — {note['Title']}")
        html = _PRACTICE_HTML.replace("__MODE__", mode).replace(
            "__LSA_DATA__",
            json.dumps(self._practice.payload(), ensure_ascii=False),
        )
        self._set_html(html)

    # -- practice-page state (compat: extract.py and the self-test read
    #    these off the window, as they did off the old PracticeDialog) --

    @property
    def mode(self) -> str | None:
        return self._practice.mode if self._practice else None

    @property
    def selection(self) -> dict | None:
        return self._practice.selection if self._practice else None

    @selection.setter
    def selection(self, value: dict | None) -> None:
        if self._practice is not None:
            self._practice.selection = value

    @property
    def _article(self):
        return self._practice.note if self._practice else None

    @property
    def _lines(self) -> list[str]:
        return self._practice.lines if self._practice else []

    @property
    def _translations(self) -> list[str]:
        return self._practice.translations if self._practice else []

    # -- lifecycle ----------------------------------------------------

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        # Decision D8 / spec: closing the Hub never writes progress.
        global _hub
        if _hub is self:
            _hub = None
        super().closeEvent(event)

    # -- bridge -------------------------------------------------------
    # JS side lives in web/list.html and web/practice.html; commands must
    # match the contract comment at the top of this module.

    def _on_bridge(self, cmd: str) -> None:
        log = self.bridge_log
        log.append(cmd[:120])
        if len(log) > 8:
            del log[: len(log) - 8]
        try:
            page = self._page
            if cmd.startswith("lsa:open:"):
                if page != "list":
                    # Stale navigation from a page already swapped away
                    # (e.g. a double-clicked row): the first command won.
                    return
                payload = cmd[len("lsa:open:"):]
                nid_s, sep, mode = payload.partition(":")
                if not sep or mode not in MODES:
                    return
                self.show_practice(int(nid_s), mode)
            elif cmd == "lsa:back":
                if page != "practice":
                    return
                self.show_list()
            elif page != "practice" or self._practice is None:
                # Stale practice command after a swap to the list: one page
                # guard covers sel / extract / play alike.
                return
            elif cmd.startswith("lsa:sel:"):
                payload = cmd[len("lsa:sel:"):]
                self._practice.selection = (
                    None if payload in ("null", "-") else json.loads(payload)
                )
            elif cmd == "lsa:extract":
                from . import extract

                extract.run_extract(self)
            elif cmd.startswith("lsa:play:"):
                idx = int(cmd.split(":", 2)[2])
                self._practice.play_line(idx)
        except Exception:
            print("language_study_anki: bridge error:\n" + traceback.format_exc())


# --------------------------------------------------------------- entry


def open_hub(
    parent=None, note_id: int | None = None, mode: str | None = None
) -> HubWindow:
    """Open (or raise) the singleton Hub; with ``note_id`` land on that
    article's practice page, otherwise open on — or keep — the list page.

    Repeated Tools-menu choices raise the existing window regardless of the
    page it shows (spec: practice-hub → Tools-menu entry).
    """
    global _hub
    hub = _hub
    if hub is not None:
        try:
            if note_id is not None:
                hub.show_practice(note_id, mode)
            _raise(hub)
            return hub
        except RuntimeError:
            _hub = hub = None  # C++ object already deleted
    from aqt import mw

    hub = HubWindow(parent, mw, note_id, mode)
    _hub = hub
    hub.show()
    hub.raise_()
    hub.activateWindow()
    return hub


def _raise(hub: HubWindow) -> None:
    """Make an existing Hub visible and focused, restoring it from the
    minimized state without disturbing a maximized one."""
    hub.show()
    if hub.isMinimized():
        hub.showNormal()
    hub.raise_()
    hub.activateWindow()


def register() -> None:
    """Tools-menu entry (spec: practice-hub → Tools-menu entry)."""
    from aqt import mw
    from aqt.qt import QAction

    if mw is None:
        return
    # Addon reload must not duplicate the action (bootstrap's guard covers
    # hook registrations; this one lives on the menu itself).
    if mw.form.menuTools.findChild(QAction, _MENU_OBJECT_NAME) is not None:
        return
    action = QAction(MENU_LABEL, mw)
    action.setObjectName(_MENU_OBJECT_NAME)
    action.triggered.connect(_on_menu_triggered)
    mw.form.menuTools.addAction(action)


def _on_menu_triggered() -> None:
    try:
        from aqt import mw

        if mw is None or getattr(mw, "col", None) is None:
            from aqt.utils import tooltip

            tooltip("Open a profile first.")
            return
        open_hub(mw)
    except Exception:
        print("language_study_anki: hub menu failed:\n" + traceback.format_exc())
