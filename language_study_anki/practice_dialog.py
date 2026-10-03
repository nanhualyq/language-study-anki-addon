"""Practice dialog: one QWebEngine window, four skill modes.

Specs: practice-dialog (entry, rendering, scroll restore, selection capture).
Decision D4: mode is a rendering flag; Python owns progress I/O, TTS requests
and extraction. No progress writes happen here — scrolling and dialog close
never write (decision D8): the dialog only READS the mode's progress field.
"""

from __future__ import annotations

import json
import traceback

from aqt.qt import QDialog, QVBoxLayout

from . import tts
from .progress import get_progress, progress_field
from .provisioning import ARTICLE_NOTE_TYPE
from .suspension import ensure_note_suspended
from .storage import field_to_lines

MODES = ("listening", "speaking", "reading", "writing")
MODE_LABELS = {
    "listening": "Practice: Listening",
    "speaking": "Practice: Speaking",
    "reading": "Practice: Reading",
    "writing": "Practice: Writing",
}

# Set/kept by open(); prevents GC and duplicate windows per note+mode.
_open: dict[tuple[int, str], "PracticeDialog"] = {}


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


_HTML = r"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body { font-family: sans-serif; margin: 0; background: #fafafa; color: #222; }
#toolbar { position: sticky; top: 0; background: #fff; border-bottom: 1px solid #ddd;
  padding: 8px 14px; display: flex; gap: 12px; align-items: center; z-index: 5; }
#toolbar .field { color: #888; font-size: 12px; }
.line { display: flex; gap: 10px; padding: 7px 14px; align-items: flex-start;
  border-bottom: 1px solid #f0f0f0; }
.line.learned { background: #f2f9f2; }
.line.learned .ln { color: #4a4; }
.play { flex: 0 0 auto; border: 1px solid #bbb; background: #fff; border-radius: 4px;
  cursor: pointer; padding: 2px 8px; font-size: 12px; }
.body { flex: 1 1 auto; min-width: 0; }
.primary { white-space: pre-wrap; line-height: 1.5; }
.secondary { display: none; color: #666; font-size: 13px; margin-top: 3px;
  white-space: pre-wrap; line-height: 1.5; }
.ln { flex: 0 0 34px; text-align: right; color: #bbb; font-size: 11px; padding-top: 3px; }
.empty { padding: 60px 20px; text-align: center; color: #888; font-size: 18px; }
/* mode rules */
body.mode-listening .primary { display: none; }
body.mode-listening .line.expanded .primary { display: block; }
body.mode-speaking .primary { display: block; }
body.mode-reading .primary { display: block; }
body.mode-reading.show-trans .secondary { display: block; }
body.mode-writing .primary { display: block; }
body.mode-writing .line .secondary.source { display: none; }
body.mode-writing .line.revealed .secondary.source { display: block; }
#trans-toggle { display: none; }
body.mode-reading #trans-toggle { display: inline-block; }
.hint { position: fixed; bottom: 8px; right: 14px; color: #aaa; font-size: 11px; }
</style></head>
<body class="mode-__MODE__">
<div id="toolbar">
  <strong id="mode-name">__MODE__</strong>
  <span class="field" id="pf"></span>
  <button id="trans-toggle">Show translation</button>
</div>
<div id="app"></div>
<div class="hint">select text &amp; press Ctrl+E to extract</div>
<script>
const D = __LSA_DATA__;
document.getElementById('pf').textContent = D.progressField + ':' + D.progress;

function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
const hasTrans = D.translations.length > 0;
const showPlay = D.mode === 'listening' || D.mode === 'speaking';

const app = document.getElementById('app');
if (D.lines.length === 0) {
  app.innerHTML = '<div class="empty">Article content is empty</div>';
} else {
  const learnedTo = Math.min(D.progress || 0, D.lines.length);
  let html = '';
  for (let i = 1; i <= D.lines.length; i++) {
    const src = D.lines[i-1];
    const tr = D.translations[i-1] || '';
    let main;
    if (D.mode === 'writing' && hasTrans) {
      /* Flutter parity: selection targets the TRANSLATION; the revealed
         source line is view-only. */
      main = '<div class="primary sel-area">' + esc(tr) + '</div>' +
             '<div class="secondary source">' + esc(src) + '</div>';
    } else {
      main = '<div class="primary sel-area">' + esc(src) + '</div>' +
             '<div class="secondary">' + esc(tr) + '</div>';
    }
    html += '<div class="line' + (i <= learnedTo ? ' learned' : '') +
            '" data-line="' + i + '">' +
            (showPlay ? '<button class="play" data-play="' + i + '">&#9654;</button>' : '') +
            '<div class="body">' + main + '</div>' +
            '<div class="ln">' + i + '</div></div>';
  }
  app.innerHTML = html;
  // Restore scroll: retry — QWebEngine may not have a scrollable range yet
  // when the script first runs (dialog still laying out), which silently
  // no-ops scrollTo.
  if (learnedTo > 0) {
    let tries = 0;
    (function tryScroll(){
      const row = app.querySelector('[data-line="' + learnedTo + '"]');
      if (row) window.scrollTo(0, Math.max(0, row.offsetTop - 60));
      const at = window.scrollY || document.scrollingElement.scrollTop || 0;
      if (at === 0 && tries++ < 25) setTimeout(tryScroll, 100);
    })();
  }
}

/* Live learned-style update after an extract (Python owns the write; this
   reflects the new progress immediately instead of on next open). */
window.markLearnedUpTo = function(n){
  for (let i = 1; i <= n && i <= D.lines.length; i++) {
    const r = app.querySelector('[data-line="' + i + '"]');
    if (r) r.classList.add('learned');
  }
  D.progress = Math.max(D.progress || 0, n);
};

document.getElementById('trans-toggle').addEventListener('click', function(){
  document.body.classList.toggle('show-trans');
  this.textContent = document.body.classList.contains('show-trans')
    ? 'Hide translation' : 'Show translation';
});

app.addEventListener('click', function(e){
  const p = e.target.closest('[data-play]');
  if (p) { pycmd('lsa:play:' + p.dataset.play); return; }
  const row = e.target.closest('.line');
  if (!row) return;
  /* Selecting text or clicking on text must never toggle visibility
     (bug fixed: expanded/revealed content hid on every selection click). */
  const s = window.getSelection();
  if (s && s.toString().length > 0) return;
  /* In writing, clicks on the (selectable) translation still toggle the
     source reveal — only listening/speaking/reading guard text clicks. */
  if (D.mode !== 'writing' && e.target.closest('.sel-area')) return;
  if (D.mode === 'listening') row.classList.toggle('expanded');
  else if (D.mode === 'writing') row.classList.toggle('revealed');
});

/* ---- selection capture (single-line, within a .sel-area) ---- */
function sendSel(obj){
  pycmd('lsa:sel:' + (obj ? JSON.stringify(obj) : 'null'));
}
function computeSel(){
  const s = window.getSelection();
  if (!s || s.isCollapsed || s.rangeCount === 0) return null;
  const r = s.getRangeAt(0);
  let el = r.commonAncestorContainer;
  if (el.nodeType === 3) el = el.parentElement;
  /* Row first: a whole-line selection can put range endpoints on the row
     element itself (or the line-number chrome), which made closest('.sel-area')
     fail and whole-line extraction impossible. */
  const row = el.closest ? el.closest('.line') : null;
  if (!row) return null;
  const area = row.querySelector('.sel-area');
  if (!area) return null;
  const full = document.createRange();
  full.selectNodeContents(area);
  const areaLen = area.textContent.length;
  let start = 0, end = areaLen;
  if (area.contains(r.startContainer)) {
    const a = full.cloneRange();
    a.setEnd(r.startContainer, r.startOffset);
    start = a.toString().length;
  }
  if (area.contains(r.endContainer)) {
    const b = full.cloneRange();
    b.setEnd(r.endContainer, r.endOffset);
    end = b.toString().length;
  }
  if (end <= start) return null;
  const text = area.textContent.substring(start, end);
  if (!text) return null;
  return {line: +row.dataset.line, start: start, end: end, text: text};
}
document.addEventListener('selectionchange', function(){
  sendSel(computeSel());
});

/* ---- Ctrl+E ---- */
document.addEventListener('keydown', function(e){
  if ((e.ctrlKey || e.metaKey) && (e.key === 'e' || e.key === 'E')) {
    e.preventDefault();
    pycmd('lsa:extract');
  }
});
</script>
</body></html>"""
