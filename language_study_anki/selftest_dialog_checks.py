"""Practice-dialog runtime checks (selftest; specs 4.x / 5.4 / 5.5 / 3.2).

These drive the real dialog webview: rendering per mode, scroll restore,
selection capture, TTS, and the extract flow including progress writes.
"""

from __future__ import annotations
import json
import time
import traceback

from . import provisioning, tts
from .progress import get_progress
from .selftest import after_delay
from .selftest_checks import _close_add_dialog
from .suspension import ensure_note_suspended
from .storage import lines_to_field

# 40 lines: content must EXCEED the ~700px viewport, otherwise scroll
# restore is unobservable (evidence: 12-line fixture gave bodyH=502 < viewport
# and scrollY stayed 0 — nothing to scroll).
LINES12 = [f"Source sentence number {i} for scrolling tests." for i in range(1, 41)]
TRANS12 = [f"用于滚动测试的第{i}行源句。" for i in range(1, 41)]

# ---------------------------------------------------------------- fixtures


COVER_VALUE = "cover-selftest.jpg"


def _ensure_article_cover_field(col) -> bool:
    """Add the user-maintained Cover field to LSA-Article if absent.

    The addon does NOT provision Cover on articles (proposal: it is user-
    maintained); simulate the user's collection here so extraction has a
    source value to copy. Returns True when the field exists afterwards.
    """
    mm = col.models
    model = mm.by_name(provisioning.ARTICLE_NOTE_TYPE)
    if model is None:
        return False
    if not any(f["name"] == "Cover" for f in model["flds"]):
        mm.add_field(model, mm.new_field("Cover"))
        if hasattr(mm, "update_dict"):
            mm.update_dict(model)
    return True


def _ensure_long_article(col) -> int:
    from .storage import field_to_lines

    model = provisioning.ensure_article_notetype(col)  # idempotent
    _ensure_article_cover_field(col)
    found = col.find_notes('Title:"LSA long article"')
    if found:
        nid = next(iter(found))
        note = col.get_note(nid)
        try:
            # Refresh if the fixture predates a line-count change (must exceed
            # the viewport for scroll-restore to be observable).
            if len(field_to_lines(note["Content"])) != len(LINES12):
                note["Content"] = lines_to_field(LINES12)
                note["Translation"] = lines_to_field(TRANS12)
                note.flush()
            if note["Cover"] != COVER_VALUE:
                note["Cover"] = COVER_VALUE
                note.flush()
            return nid
        except (KeyError, IndexError):
            # Stale note predating the Cover field — drop and recreate below.
            col.remove_notes([nid])
    note = col.new_note(model)
    note["Title"] = "LSA long article"
    note["Content"] = lines_to_field(LINES12)
    note["Translation"] = lines_to_field(TRANS12)
    note["Url"] = "https://example.com/long"
    note["Cover"] = COVER_VALUE
    col.add_note(note, provisioning.ensure_deck(col, provisioning.EXTRACT_DECK))
    ensure_note_suspended(note)
    return note.id


def _ensure_nocover_article(col) -> int:
    """An article carrying an empty Cover (empty-fallback extract scenario)."""
    model = provisioning.ensure_article_notetype(col)
    _ensure_article_cover_field(col)
    found = col.find_notes('Title:"LSA nocover article"')
    if found:
        return next(iter(found))
    note = col.new_note(model)
    note["Title"] = "LSA nocover article"
    note["Content"] = lines_to_field(LINES12)
    note["Url"] = "https://example.com/nocover"
    note["Cover"] = ""
    col.add_note(note, provisioning.ensure_deck(col, provisioning.EXTRACT_DECK))
    ensure_note_suspended(note)
    return note.id


def _ensure_empty_article(col) -> int:
    found = col.find_notes('Title:"LSA empty article"')
    if found:
        return next(iter(found))
    model = provisioning.ensure_article_notetype(col)
    note = col.new_note(model)
    note["Title"] = "LSA empty article"
    note["Content"] = ""
    col.add_note(note, provisioning.ensure_deck(col, provisioning.EXTRACT_DECK))
    ensure_note_suspended(note)
    return note.id


def _set_progress_raw(col, note_id: int, skill: str, value: int) -> None:
    from .progress import progress_field

    note = col.get_note(note_id)
    note[progress_field(skill)] = str(value)
    note.flush()


def _js(dialog, code, cb) -> None:
    dialog.web.page().runJavaScript(code, cb)


# ---------------------------------------------------------------- 4.1 menu


def check_browser_menu(mw, report, done) -> None:
    try:
        from .browser_menu import build_menu_labels

        col = mw.col
        art = _ensure_long_article(col)
        prov = provisioning.provision(col)
        basic = col.new_note(prov["extract_notetypes"]["LSA-ReadWrite"])
        basic["Front"] = "not an article"
        col.add_note(basic, prov["extract_deck_id"])

        labels = build_menu_labels([art], col)
        mixed = build_menu_labels([art, basic.id], col)
        other = build_menu_labels([basic.id], col)
        none_sel = build_menu_labels([], col)

        # Expected percentages re-derived from the fixture's own progress
        # fields and Content line count (labels show the FIRST note = art).
        from .practice_dialog import MODES, MODE_LABELS
        from .storage import field_to_lines

        note = col.get_note(art)
        total = len(field_to_lines(note["Content"]))

        def pct(skill: str) -> int:
            line = get_progress(note, skill)
            if total <= 0 or line <= 0:
                return 0
            if line >= total:
                return 100
            return int(line * 100.0 / total + 0.5)

        expected = [
            (mode, f"{MODE_LABELS[mode]} ({pct(mode)}%)") for mode in MODES
        ]
        report["ok"] = (
            labels == expected
            and mixed is None
            and other is None
            and none_sel is None
        )
        report["detail"] = {
            "labels": labels,
            "mixed_is_none": mixed is None,
            "non_article_is_none": other is None,
            "empty_is_none": none_sel is None,
        }
    except Exception:
        report["ok"] = False
        report["detail"] = traceback.format_exc()
    done()


# ---------------------------------------------------------------- 4.2 modes

_JS_EMPTY = (
    "(document.querySelector('.empty')||{textContent:'<none>'}).textContent"
)
_JS_READING = (
    "var sec=document.querySelector('.line .secondary');"
    "var s0=getComputedStyle(sec).display;"
    "document.querySelector('.line .body').click();"
    "var s0row=getComputedStyle(sec).display;"
    "var tw=document.querySelector('[data-line=\"1\"] [data-twisty]');"
    "if(tw) tw.click();"
    "var s3=getComputedStyle(sec).display;"
    "JSON.stringify({"
    "rows: document.querySelectorAll('.line').length,"
    "primary: getComputedStyle(document.querySelector('.line .primary')).display,"
    "s0: s0, s0row: s0row, s3: s3,"
    "twisty: !!tw,"
    "toggle: !!document.getElementById('trans-toggle')"
    "})"
)
_JS_LISTENING = (
    "var p=document.querySelector('.line .primary');"
    "var before=getComputedStyle(p).display;"
    "document.querySelector('.line .body').click();"
    "var afterRow=getComputedStyle(p).display;"
    "var tw=document.querySelector('[data-twisty]');"
    "if(tw) tw.click();"
    "JSON.stringify({before:before, afterRow:afterRow, twisty:!!tw,"
    "after:getComputedStyle(p).display})"
)
_JS_WRITING = (
    "var p=document.querySelector('.line .primary');"
    "var src=document.querySelector('.line .secondary.source');"
    "var text0=p.textContent;"
    "var srcBefore=getComputedStyle(src).display;"
    "document.querySelector('.line .body').click();"
    "var srcAfterRow=getComputedStyle(src).display;"
    "var tw=document.querySelector('[data-twisty]');"
    "if(tw) tw.click();"
    "JSON.stringify({text0:text0, srcBefore:srcBefore, twisty:!!tw,"
    "srcAfterRow:srcAfterRow, srcAfter:getComputedStyle(src).display})"
)
_JS_SPEAKING = (
    "var sec=document.querySelector('.line .secondary');"
    "var before=getComputedStyle(sec).display;"
    "var tw=document.querySelector('[data-twisty]');"
    "if(tw) tw.click();"
    "JSON.stringify({"
    "primary: getComputedStyle(document.querySelector('.line .primary')).display,"
    "play: !!document.querySelector('.play'), twisty: !!tw, before: before,"
    "after:getComputedStyle(sec).display})"
)


def _ev_empty(payload):
    return payload.strip() == "Article content is empty", payload


def _ev_reading(payload):
    d = json.loads(payload)
    ok = (
        d["rows"] == len(LINES12)
        and d["primary"] != "none"
        # closed by default, and a plain row click must not reveal it
        and d["s0"] == "none"
        and d["s0row"] == "none"
        # the row's own twisty opens just that row
        and d["twisty"]
        and d["s3"] != "none"
        # no bulk toolbar toggle exists any more
        and not d["toggle"]
    )
    return ok, d


def _ev_listening(payload):
    d = json.loads(payload)
    ok = (
        d["before"] == "none"
        and d["twisty"]
        and d["afterRow"] == "none"   # row click never toggles
        and d["after"] != "none"       # twisty does
    )
    return ok, d


def _ev_writing(payload):
    d = json.loads(payload)
    ok = (
        d["text0"] == TRANS12[0]
        and d["twisty"]
        and d["srcBefore"] == "none"
        and d["srcAfterRow"] == "none"  # row click never toggles
        and d["srcAfter"] != "none"      # twisty does
    )
    return ok, d


def _ev_speaking(payload):
    d = json.loads(payload)
    ok = (
        d["primary"] != "none"
        and d["play"]
        and d["twisty"]
        and d["before"] == "none"
        and d["after"] != "none"
    )
    return ok, d


def check_dialog_modes(mw, report, done) -> None:
    """Task 4.2: mode-specific rendering incl. the empty state."""
    from .practice_dialog import open_dialog

    col = mw.col
    art = _ensure_long_article(col)
    empty = _ensure_empty_article(col)
    result = report["detail"] = {}

    stages = [
        ("empty", empty, "reading", _JS_EMPTY, _ev_empty),
        ("reading", art, "reading", _JS_READING, _ev_reading),
        ("listening", art, "listening", _JS_LISTENING, _ev_listening),
        ("writing", art, "writing", _JS_WRITING, _ev_writing),
        ("speaking", art, "speaking", _JS_SPEAKING, _ev_speaking),
    ]

    def run_stage(i: int) -> None:
        if i >= len(stages):
            report["ok"] = all(v.get("ok") for v in result.values())
            done()
            return
        name, nid, mode, js, evaluate = stages[i]
        dlg = open_dialog(None, nid, mode)

        def probed(payload):
            try:
                ok, detail = evaluate(payload)
            except Exception:
                ok, detail = False, traceback.format_exc()
            result[name] = {"ok": ok, "detail": detail}
            try:
                dlg.close()
            except Exception:
                pass
            after_delay(400, lambda: run_stage(i + 1))

        after_delay(1200, lambda: _js(dlg, js, probed))

    run_stage(0)


# ---------------------------------------------------------------- 4.3 restore


def check_dialog_restore(mw, report, done) -> None:
    """Task 4.3: scroll restore + learned styling + clamping."""
    from .practice_dialog import open_dialog

    col = mw.col
    art = _ensure_long_article(col)
    result = report["detail"] = {}

    seq = [(0, "no_history"), (5, "restore_at_5"), (999, "clamp_beyond")]

    def run_step(i: int) -> None:
        if i >= len(seq):
            report["ok"] = all(
                result.get(tag, {}).get("ok") for _, tag in seq
            )
            done()
            return
        value, tag = seq[i]
        _set_progress_raw(col, art, "reading", value)
        dlg = open_dialog(None, art, "reading")

        def probed(payload):
            d = json.loads(payload)
            expected = min(value, len(LINES12))
            ok = d["learned"] == expected
            if value > 0:
                ok = ok and d["scroll"] > 0
            else:
                ok = ok and d["scroll"] == 0 and d["learned"] == 0
            d["ok"] = ok
            result[tag] = d
            try:
                dlg.close()
            except Exception:
                pass
            after_delay(400, lambda: run_step(i + 1))

        js = (
            "JSON.stringify({"
            "scroll: Math.round(window.scrollY || (document.scrollingElement"
            " ? document.scrollingElement.scrollTop : 0)),"
            "scrollEl: (document.scrollingElement || {}).tagName || '?',"
            "learned: document.querySelectorAll('.line.learned').length,"
            "total: document.querySelectorAll('.line').length,"
            "bodyH: document.body.scrollHeight"
            "})"
        )
        after_delay(1300, lambda: _js(dlg, js, probed))

    run_step(0)


# ---------------------------------------------------------------- 4.4 selection


def check_selection_capture(mw, report, done) -> None:
    """Task 4.4: JS → Python selection capture and clearing."""
    from .practice_dialog import open_dialog

    col = mw.col
    art = _ensure_long_article(col)
    dlg = open_dialog(None, art, "reading")
    result = report["detail"] = {}

    def finish(ok):
        report["ok"] = ok
        try:
            dlg.close()
        except Exception:
            pass
        done()

    js_select = (
        "(function(){"
        "var row=document.querySelector('[data-line=\"7\"] .sel-area');"
        "if(!row) return 'no-row';"
        "var t=row.firstChild;"
        "var r=document.createRange();"
        "r.setStart(t,0); r.setEnd(t,6);"
        "var s=getSelection(); s.removeAllRanges(); s.addRange(r);"
        "document.dispatchEvent(new Event('selectionchange'));"
        "return 'sent';})()"
    )

    def on_sent(payload):
        result["js_sent"] = payload
        after_delay(600, check_state)

    def check_state():
        sel = dlg.selection
        result["selection"] = sel
        ok = (
            isinstance(sel, dict)
            and sel.get("line") == 7
            and sel.get("start") == 0
            and sel.get("end") == 6
            and sel.get("text") == LINES12[6][:6]
        )
        if not ok:
            finish(False)
            return

        def check_cleared():
            result["after_clear"] = dlg.selection
            result["bridge_log"] = list(getattr(dlg, "bridge_log", []))
            finish(dlg.selection is None)

        def on_clear_sent(payload):
            result["clear_js"] = payload
            after_delay(900, check_cleared)

        _js(
            dlg,
            "(function(){getSelection().removeAllRanges();"
            "document.dispatchEvent(new Event('selectionchange'));"
            "return 'x';})()",
            on_clear_sent,
        )

    after_delay(1300, lambda: _js(dlg, js_select, on_sent))


# ---------------------------------------------------------------- 4.5 / 1.3 tts


def check_tts(mw, report, done) -> None:
    """Tasks 4.5 + 1.3: non-blocking speak, cache reuse, interrupt."""
    result = report["detail"] = {}
    try:
        import subprocess as _sp

        synthesis: list = []
        orig_popen = _sp.Popen
        orig_run = _sp.run

        def is_synth(cmd) -> bool:
            low = str(cmd).lower()
            return "spvoice" in low or "system.speech" in low

        def spy_popen(cmd, *a, **k):
            if is_synth(cmd):
                synthesis.append(str(cmd)[:200])
            return orig_popen(cmd, *a, **k)

        def spy_run(cmd, *a, **k):
            if is_synth(cmd):
                synthesis.append(str(cmd)[:200])
            return orig_run(cmd, *a, **k)

        _sp.Popen = spy_popen
        _sp.run = spy_run

        text = "The quick brown fox jumps over the lazy dog."
        t0 = time.monotonic()
        tts.speak(text)
        t1 = time.monotonic()

        def second():
            tts.speak(text)  # identical text → cached synthesis expected
            after_delay(2500, third)

        def third():
            tts.speak("Another line entirely for interruption testing.")
            after_delay(1500, finalize)

        def finalize():
            try:
                tts.stop()
            except Exception:
                pass
            _sp.Popen = orig_popen
            _sp.run = orig_run
            result["speak_ms"] = round((t1 - t0) * 1000)
            result["synthesis_spawns"] = synthesis
            result["synthesis_count"] = len(synthesis)
            # speak() must return fast (non-blocking); two identical calls +
            # one different → at most 2 synthesis spawns (cache for the dup).
            report["ok"] = result["speak_ms"] < 1000 and len(synthesis) <= 2
            done()

        after_delay(2500, second)
        result["speak_ms_first"] = round((t1 - t0) * 1000)
    except Exception:
        report["ok"] = False
        result["error"] = traceback.format_exc()
        done()


# ---------------------------------------------------------------- 5.4/5.5/3.2


EXTRACT_ROUNDS = [
    # (mode, line, note type, required tokens, article key, expected Cover)
    ("reading", 8, "LSA-ReadWrite",
     ["front:source", "highlight:mark", "back:"], "main", COVER_VALUE),
    ("listening", 10, "LSA-Listen",
     ["front:source", "highlight:???", "back:selection", "phone:"],
     "main", COVER_VALUE),
    ("speaking", 12, "LSA-Speak",
     ["front:source", "highlight:mark", "mark:mic", "back:selection", "phone:"],
     "main", COVER_VALUE),
    ("writing", 14, "LSA-ReadWrite",
     ["front:translation", "back:source-line", "lookup:skipped"],
     "main", COVER_VALUE),
    # Cover empty-fallback: an article with an empty Cover extracts "".
    ("reading", 8, "LSA-ReadWrite",
     ["front:source"], "nocover", ""),
]


def _read_add_dialog_cover(new_add_ids):
    """Cover of the prefilled note in a freshly opened Add dialog, or a
    sentinel explaining why it could not be read."""
    from aqt.qt import QApplication

    if not new_add_ids:
        return None
    target = next(
        (w for w in QApplication.topLevelWidgets() if id(w) in new_add_ids), None
    )
    if target is None:
        return "<no-add-dialog>"
    ed_note = getattr(getattr(target, "editor", None), "note", None)
    if ed_note is None:
        return "<no-editor-note>"
    try:
        return ed_note["Cover"]
    except (KeyError, IndexError):
        return "<missing>"


def check_extract_all_modes(mw, report, done) -> None:
    """Tasks 5.4 + 5.5 + 3.2 across ALL four modes (+ Cover copy/fallback).

    Per mode: capture selection (fails fast — the reported 'other modes do
    nothing' bug), fire `a`, assert the Add dialog opened, the mode's
    progress advanced to the extract line, the per-mode note type was used,
    the article's Cover was copied into the prefilled note, and no error hit
    the extract log.
    """
    from .practice_dialog import open_dialog
    from .progress import PROGRESS_FIELDS
    from aqt.qt import QApplication

    col = mw.col
    articles = {
        "main": _ensure_long_article(col),        # article carries Cover
        "nocover": _ensure_nocover_article(col),  # article Cover is empty
    }
    for aid in articles.values():
        for s in PROGRESS_FIELDS:
            _set_progress_raw(col, aid, s, 0)
    result = report["detail"] = {"rounds": []}

    fire_js = (
        "(function(){document.dispatchEvent(new KeyboardEvent('keydown',"
        "{key:'a',bubbles:true,cancelable:true}));"
        "return 'fired';})()"
    )

    def visible_adds(baseline):
        return {
            id(w)
            for w in QApplication.topLevelWidgets()
            if "Add" in type(w).__name__ and w.isVisible()
        } - baseline

    def finalize():
        note = col.get_note(articles["main"])
        final = {s: get_progress(note, s) for s in PROGRESS_FIELDS}
        result["final_progress"] = final
        # Progress assertions only track the rounds run against the main
        # article; the Cover fallback round runs on a separate article.
        expected = {
            m: ln for m, ln, _, _, key, _ in EXTRACT_ROUNDS if key == "main"
        }
        report["ok"] = all(r.get("ok") for r in result["rounds"]) and all(
            final[s] == expected[s] for s in expected
        )
        done()

    def round_start(i: int):
        if i >= len(EXTRACT_ROUNDS):
            finalize()
            return
        mode, line, nt, required, art_key, expect_cover = EXTRACT_ROUNDS[i]
        state = {
            "mode": mode,
            "line": line,
            "nt": nt,
            "required": required,
            "art_id": articles[art_key],
            "expect_cover": expect_cover,
            "round": i,
            "dlg": open_dialog(None, articles[art_key], mode),
            "baseline": {
                id(w)
                for w in QApplication.topLevelWidgets()
                if "Add" in type(w).__name__ and w.isVisible()
            },
        }
        after_delay(1500, lambda: do_select(state))

    def do_select(state):
        ln = state["line"]
        js = (
            "(function(){"
            f"var row=document.querySelector('[data-line=\"{ln}\"] .sel-area');"
            "if(!row) return 'no-row';"
            # Reveal the hidden text first: in Listening/Writing the target is
            # not rendered (display:none) until the row's twisty opens it.
            f"var tw=document.querySelector('[data-line=\"{ln}\"] [data-twisty]');"
            "if(tw) tw.click();"
            "var t=row.firstChild;"
            "var r=document.createRange(); r.setStart(t,0); r.setEnd(t,7);"
            "var s=getSelection(); s.removeAllRanges(); s.addRange(r);"
            "document.dispatchEvent(new Event('selectionchange'));"
            "return 'sent';})()"
        )
        _js(state["dlg"], js, lambda p: on_selected(state, p))

    def on_selected(state, payload):
        state["js_sent"] = payload
        after_delay(700, lambda: check_selection(state))

    def check_selection(state):
        sel = state["dlg"].selection
        state["python_sel"] = sel
        if not isinstance(sel, dict) or sel.get("line") != state["line"]:
            # The reported bug: selection never reaches Python in this mode.
            state["ok"] = False
            state["fail"] = "selection not captured"
            end_round(state)
            return
        _js(state["dlg"], fire_js, lambda p: on_fired(state, p))

    def on_fired(state, payload):
        state["fired"] = payload
        after_delay(8000, lambda: verify(state))

    def verify(state):
        new_add = visible_adds(state["baseline"])
        state["add_opened"] = bool(new_add)
        note = col.get_note(state["art_id"])
        state["progress"] = get_progress(note, state["mode"])
        state["extract_log"] = list(getattr(state["dlg"], "extract_log", []))
        state["cover"] = _read_add_dialog_cover(new_add)
        state["ok"] = (
            bool(new_add)
            and state["progress"] == state["line"]
            and f"note_type:{state['nt']}" in state["extract_log"]
            and state["cover"] == state["expect_cover"]
            and not any("ERR:" in e for e in state["extract_log"])
            and all(
                tok in " | ".join(state["extract_log"])
                for tok in state["required"]
            )
        )
        end_round(state)

    def end_round(state):
        entry = {
            k: state[k]
            for k in (
                "mode", "line", "add_opened", "progress", "cover",
                "expect_cover", "extract_log", "python_sel", "ok", "fail",
            )
            if k in state
        }
        result["rounds"].append(entry)
        try:
            state["dlg"].close()
        except Exception:
            pass
        new_add = visible_adds(state["baseline"])
        nxt = lambda: round_start(state["round"] + 1)
        if new_add:
            target = next(
                w for w in QApplication.topLevelWidgets() if id(w) in new_add
            )
            _close_add_dialog(target, nxt)
        else:
            after_delay(300, nxt)

    round_start(0)


# ---------------------------------------------------------------------- \
# gray learned-row style (change: gray-learned-row-style)
# ----------------------------------------------------------------------


def check_learned_style(mw, report, done) -> None:
    """gray-learned-row-style: learned rows carry a gray background band.

    Verifies the spec delta: gray tint perceivable in Listening mode (where a
    closed learned row shows no text), full opacity + unchanged line-number
    color, toggle/play/selection/extract on a learned row, live graying after
    an extract, and no tint without progress.
    """
    from .practice_dialog import open_dialog
    from aqt.qt import QApplication

    col = mw.col
    art = _ensure_long_article(col)
    result = report["detail"] = {}
    result["live_gray"] = {}
    GRAY = "rgb(241, 241, 242)"  # #f1f1f2 learned-row tint
    state = {}

    # -- Stage A: listening, progress 15 (learned rows show NO text) -------

    def open_listening():
        _set_progress_raw(col, art, "listening", 15)
        state["dlg_a"] = open_dialog(None, art, "listening")
        after_delay(1300, lambda: _js(state["dlg_a"], js_a, ev_a))

    # Probe computed styles learned-vs-unlearned, then exercise toggle,
    # selection, and play ON a learned row.
    js_a = (
        "(function(){"
        "var lr=document.querySelector('.line.learned');"
        "var ur=document.querySelector('[data-line=\"20\"]');"
        "var p=lr.querySelector('.primary');"
        "var before=getComputedStyle(p).display;"
        "var tw=lr.querySelector('[data-twisty]');"
        "if(tw) tw.click();"
        "var after=getComputedStyle(p).display;"
        "var area=lr.querySelector('.sel-area');"
        "var t=area.firstChild; var r=document.createRange();"
        "r.setStart(t,0); r.setEnd(t,6);"
        "var s=getSelection(); s.removeAllRanges(); s.addRange(r);"
        "document.dispatchEvent(new Event('selectionchange'));"
        "var play=lr.querySelector('.play'); if(play) play.click();"
        "return JSON.stringify({"
        "total: document.querySelectorAll('.line').length,"
        "learned: document.querySelectorAll('.line.learned').length,"
        "learnedBg: getComputedStyle(lr).backgroundColor,"
        "unlearnedBg: getComputedStyle(ur).backgroundColor,"
        "learnedOpacity: getComputedStyle(lr).opacity,"
        "unlearnedOpacity: getComputedStyle(ur).opacity,"
        "lnLearned: getComputedStyle(lr.querySelector('.ln')).color,"
        "lnUnlearned: getComputedStyle(ur.querySelector('.ln')).color,"
        "primaryBefore: before, primaryAfter: after,"
        "twisty: !!tw, play: !!play"
        "});})()"
    )

    def ev_a(payload):
        d = json.loads(payload)
        result["listening"] = d
        # Style probes are synchronous, but selection/play arrive at the
        # Python bridge via async pycmd — defer the state read (same 700ms
        # allowance check_selection_capture uses).
        after_delay(700, check_state_a)

    def check_state_a():
        d = result["listening"]
        dlg_a = state["dlg_a"]
        d["selection"] = dlg_a.selection
        d["bridge"] = list(getattr(dlg_a, "bridge_log", []))
        d["ok"] = (
            d["total"] == len(LINES12)
            and d["learned"] == 15
            # gray band perceivable with no text; unlearned rows untinted
            and d["learnedBg"] == GRAY
            and d["unlearnedBg"] != GRAY
            # no opacity reduction; line-number color unchanged
            and d["learnedOpacity"] == "1"
            and d["unlearnedOpacity"] == "1"
            and d["lnLearned"] == d["lnUnlearned"]
            # toggle reveals text on a learned row; play + selection work
            and d["primaryBefore"] == "none"
            and d["primaryAfter"] != "none"
            and d["twisty"] and d["play"]
            and isinstance(d["selection"], dict)
            and d["selection"].get("line") == 1
            and any("lsa:play:1" in e for e in d["bridge"])
        )
        try:
            dlg_a.close()
        except Exception:
            pass
        after_delay(500, open_reading)

    # -- Stage B: reading, progress 15 -> extract at line 20 ---------------

    def open_reading():
        _set_progress_raw(col, art, "reading", 15)
        state["dlg_b"] = open_dialog(None, art, "reading")
        after_delay(1300, lambda: _js(state["dlg_b"], js_b1, ev_b1))

    js_b1 = (
        "(function(){"
        "var lr=document.querySelector('.line.learned');"
        "return JSON.stringify({"
        "learned: document.querySelectorAll('.line.learned').length,"
        "learnedBg: getComputedStyle(lr).backgroundColor,"
        "primary: getComputedStyle(lr.querySelector('.primary')).display,"
        "pf: document.getElementById('pf').textContent"
        "});})()"
    )

    def ev_b1(payload):
        d = json.loads(payload)
        result["reading_band"] = d
        d["ok"] = (
            d["learned"] == 15
            and d["learnedBg"] == GRAY
            and d["primary"] != "none"
            and d["pf"] == "15/40"
        )
        _js(state["dlg_b"], js_b2, lambda p: after_delay(8000, ev_b2))

    js_b2 = (
        "(function(){"
        "var row=document.querySelector('[data-line=\"20\"] .sel-area');"
        "var t=row.firstChild; var r=document.createRange();"
        "r.setStart(t,0); r.setEnd(t,7);"
        "var s=getSelection(); s.removeAllRanges(); s.addRange(r);"
        "document.dispatchEvent(new Event('selectionchange'));"
        "document.dispatchEvent(new KeyboardEvent('keydown',"
        "{key:'a',bubbles:true,cancelable:true}));"
        "return 'fired';})()"
    )

    def ev_b2():
        d = result["extract"] = {}
        visible = {
            id(w) for w in QApplication.topLevelWidgets()
            if "Add" in type(w).__name__ and w.isVisible()
        }
        note = col.get_note(art)
        d["add_opened"] = bool(visible)
        d["progress"] = get_progress(note, "reading")
        _js(state["dlg_b"], js_b3, lambda p: ev_b3(json.loads(p), visible))

    js_b3 = (
        "(function(){"
        "var r20=document.querySelector('[data-line=\"20\"]');"
        "return JSON.stringify({"
        "hasLearnedClass: r20.classList.contains('learned'),"
        "bg: getComputedStyle(r20).backgroundColor,"
        "pf: document.getElementById('pf').textContent"
        "});})()"
    )

    def ev_b3(d, visible_adds):
        d["ok"] = (
            d["hasLearnedClass"]
            and d["bg"] == GRAY
            and d["pf"] == "20/40"
        )
        result["live_gray"]["ok"] = d["ok"]
        result["live_gray"]["detail"] = d
        result["extract"]["ok"] = (
            result["extract"]["add_opened"]
            and result["extract"]["progress"] == 20
        )
        try:
            state["dlg_b"].close()
        except Exception:
            pass
        if visible_adds:
            target = next(
                w for w in QApplication.topLevelWidgets() if id(w) in visible_adds
            )
            _close_add_dialog(target, open_clean)
        else:
            after_delay(300, open_clean)

    # -- Stage C: no progress -> no tint -----------------------------------

    def open_clean():
        _set_progress_raw(col, art, "reading", 0)
        state["dlg_c"] = open_dialog(None, art, "reading")
        after_delay(1300, lambda: _js(state["dlg_c"], js_c, ev_c))

    js_c = (
        "(function(){"
        "var r1=document.querySelector('[data-line=\"1\"]');"
        "return JSON.stringify({"
        "learned: document.querySelectorAll('.line.learned').length,"
        "bg1: getComputedStyle(r1).backgroundColor,"
        "pf: document.getElementById('pf').textContent"
        "});})()"
    )

    def ev_c(payload):
        d = json.loads(payload)
        result["no_progress"] = d
        d["ok"] = d["learned"] == 0 and d["bg1"] != GRAY and d["pf"] == "0/40"
        try:
            state["dlg_c"].close()
        except Exception:
            pass
        report["ok"] = all(
            result.get(k, {}).get("ok")
            for k in ("listening", "reading_band", "extract",
                      "live_gray", "no_progress")
        )
        done()

    open_listening()


CHECKS_EXTRA = [
    ("browser_menu", check_browser_menu),
    ("dialog_modes", check_dialog_modes),
    ("dialog_restore", check_dialog_restore),
    ("selection_capture", check_selection_capture),
    ("tts", check_tts),
    ("extract_all_modes", check_extract_all_modes),
    ("learned_style", check_learned_style),
]
