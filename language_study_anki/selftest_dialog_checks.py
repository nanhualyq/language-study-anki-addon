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


def _ensure_long_article(col) -> int:
    from .storage import field_to_lines

    found = col.find_notes('Title:"LSA long article"')
    if found:
        nid = next(iter(found))
        note = col.get_note(nid)
        # Refresh if the fixture predates a line-count change (must exceed
        # the viewport for scroll-restore to be observable).
        if len(field_to_lines(note["Content"])) != len(LINES12):
            note["Content"] = lines_to_field(LINES12)
            note["Translation"] = lines_to_field(TRANS12)
            note.flush()
        return nid
    model = provisioning.ensure_article_notetype(col)
    note = col.new_note(model)
    note["Title"] = "LSA long article"
    note["Content"] = lines_to_field(LINES12)
    note["Translation"] = lines_to_field(TRANS12)
    note["Url"] = "https://example.com/long"
    col.add_note(note, provisioning.ensure_deck(col, provisioning.ARTICLE_DECK))
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
    col.add_note(note, provisioning.ensure_deck(col, provisioning.ARTICLE_DECK))
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
        basic = col.new_note(prov["extract_notetypes"]["@Basic"])
        basic["Front"] = "not an article"
        col.add_note(basic, prov["extract_deck_id"])

        labels = build_menu_labels([art], col)
        mixed = build_menu_labels([art, basic.id], col)
        other = build_menu_labels([basic.id], col)
        none_sel = build_menu_labels([], col)
        expected = [
            ("listening", "Practice: Listening"),
            ("speaking", "Practice: Speaking"),
            ("reading", "Practice: Reading"),
            ("writing", "Practice: Writing"),
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
    "document.getElementById('trans-toggle').click();"
    "var s1=getComputedStyle(sec).display;"
    "JSON.stringify({"
    "rows: document.querySelectorAll('.line').length,"
    "primary: getComputedStyle(document.querySelector('.line .primary')).display,"
    "s0: s0, s1: s1,"
    "toggle: !!document.getElementById('trans-toggle')"
    "})"
)
_JS_LISTENING = (
    "var p=document.querySelector('.line .primary');"
    "var before=getComputedStyle(p).display;"
    "document.querySelector('.line').click();"
    "JSON.stringify({before:before, after:getComputedStyle(p).display})"
)
_JS_WRITING = (
    "var p=document.querySelector('.line .primary');"
    "var src=document.querySelector('.line .secondary.source');"
    "var text0=p.textContent;"
    "var srcBefore=getComputedStyle(src).display;"
    "document.querySelector('.line').click();"
    "JSON.stringify({text0:text0, srcBefore:srcBefore,"
    "srcAfter:getComputedStyle(src).display})"
)
_JS_SPEAKING = (
    "JSON.stringify({"
    "primary: getComputedStyle(document.querySelector('.line .primary')).display,"
    "play: !!document.querySelector('.play')"
    "})"
)


def _ev_empty(payload):
    return payload.strip() == "Article content is empty", payload


def _ev_reading(payload):
    d = json.loads(payload)
    ok = (
        d["rows"] == len(LINES12)
        and d["primary"] != "none"
        and d["s0"] == "none"
        and d["s1"] != "none"
        and d["toggle"]
    )
    return ok, d


def _ev_listening(payload):
    d = json.loads(payload)
    return d["before"] == "none" and d["after"] != "none", d


def _ev_writing(payload):
    d = json.loads(payload)
    ok = d["text0"] == TRANS12[0] and d["srcBefore"] == "none" and d["srcAfter"] != "none"
    return ok, d


def _ev_speaking(payload):
    d = json.loads(payload)
    return d["primary"] != "none" and d["play"], d


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
    # (mode, line, note type, required tokens in extract_log)
    ("reading", 8, "@Basic", ["front:source", "highlight:mark", "back:"]),
    ("listening", 10, "@EnListen",
     ["front:source", "highlight:???", "back:selection", "phone:"]),
    ("speaking", 12, "@EnSpeak",
     ["front:source", "highlight:mark", "back:selection", "phone:"]),
    ("writing", 14, "@Basic",
     ["front:translation", "back:source-line", "lookup:skipped"]),
]


def check_extract_all_modes(mw, report, done) -> None:
    """Tasks 5.4 + 5.5 + 3.2 across ALL four modes.

    Per mode: capture selection (fails fast — the reported 'other modes do
    nothing' bug), fire Ctrl+E, assert the Add dialog opened, the mode's
    progress advanced to the extract line, the per-mode note type was used,
    and no error hit the extract log.
    """
    from .practice_dialog import open_dialog
    from .progress import PROGRESS_FIELDS
    from aqt.qt import QApplication

    col = mw.col
    art = _ensure_long_article(col)
    for s in PROGRESS_FIELDS:
        _set_progress_raw(col, art, s, 0)
    result = report["detail"] = {"rounds": []}

    fire_js = (
        "(function(){document.dispatchEvent(new KeyboardEvent('keydown',"
        "{key:'e',ctrlKey:true,bubbles:true,cancelable:true}));"
        "return 'fired';})()"
    )

    def visible_adds(baseline):
        return {
            id(w)
            for w in QApplication.topLevelWidgets()
            if "Add" in type(w).__name__ and w.isVisible()
        } - baseline

    def finalize():
        note = col.get_note(art)
        final = {s: get_progress(note, s) for s in PROGRESS_FIELDS}
        result["final_progress"] = final
        expected = {m: ln for m, ln, _, _ in EXTRACT_ROUNDS}
        report["ok"] = all(r.get("ok") for r in result["rounds"]) and all(
            final[s] == expected[s] for s in expected
        )
        done()

    def round_start(i: int):
        if i >= len(EXTRACT_ROUNDS):
            finalize()
            return
        mode, line, nt, required = EXTRACT_ROUNDS[i]
        state = {
            "mode": mode,
            "line": line,
            "nt": nt,
            "required": required,
            "round": i,
            "dlg": open_dialog(None, art, mode),
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
            "row.classList.add('expanded'); row.classList.add('revealed');"
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
        note = col.get_note(art)
        state["progress"] = get_progress(note, state["mode"])
        state["extract_log"] = list(getattr(state["dlg"], "extract_log", []))
        state["ok"] = (
            bool(new_add)
            and state["progress"] == state["line"]
            and f"note_type:{state['nt']}" in state["extract_log"]
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
                "mode", "line", "add_opened", "progress",
                "extract_log", "python_sel", "ok", "fail",
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


CHECKS_EXTRA = [
    ("browser_menu", check_browser_menu),
    ("dialog_modes", check_dialog_modes),
    ("dialog_restore", check_dialog_restore),
    ("selection_capture", check_selection_capture),
    ("tts", check_tts),
    ("extract_all_modes", check_extract_all_modes),
]
