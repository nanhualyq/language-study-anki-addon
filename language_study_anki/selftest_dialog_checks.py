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


# ------------------------------------------------------------ 4.1 hub

_JS_HUB_LIST = (
    "JSON.stringify({"
    "empty: !!document.querySelector('.empty'),"
    "ids: Array.from(document.querySelectorAll('.row')).map("
    "function(r){return +r.dataset.id;}),"
    "rows: Array.from(document.querySelectorAll('.row')).map(function(r){"
    "return {title: r.querySelector('.title').textContent,"
    "skills: Array.from(r.querySelectorAll('.skill')).map("
    # each skill entry is a ring: percent lives in .pct, name in .name
    # (whole-button textContent no longer carries "<Skill> <pct>%")
    "function(s){return s.querySelector('.name').textContent + ' ' +"
    " s.querySelector('.pct').textContent;})};})"
    "})"
)

_JS_HUB_PRACTICE = (
    "JSON.stringify({"
    "back: !!document.getElementById('back'),"
    "backFirst: !!document.querySelector('#toolbar') && "
    "document.querySelector('#toolbar').firstElementChild.id === 'back',"
    "mode: (document.getElementById('mode-name')||{}).textContent,"
    "counter: (document.getElementById('pf')||{}).textContent,"
    "rows: document.querySelectorAll('.line').length"
    "})"
)

_JS_HUB_EMPTY = (
    "JSON.stringify({"
    "empty: !!document.querySelector('.empty'),"
    "rows: document.querySelectorAll('.row').length"
    "})"
)

_HUB_SKILL_LABELS = {
    "reading": "Reading",
    "speaking": "Speaking",
    "listening": "Listening",
    "writing": "Writing",
}


def check_hub_list(mw, report, done) -> None:
    """add-article-list-hub (spec: practice-hub): Tools-menu Hub, list
    rows with per-skill percentages in newest-first order, empty state,
    lsa:open / lsa:back navigation, titles, singleton, no progress writes
    on navigation, and percentage refresh after a progress write during
    practice. Replaces the removed browser-menu check."""
    from . import hub as hub_mod
    from .hub import list_html
    from .practice_dialog import MODES
    from .storage import field_to_lines

    col = mw.col
    _ensure_long_article(col)
    provisioning.provision(col)
    result = report["detail"] = {}

    # Spec: Tools-menu entry — trigger the registered action itself so this
    # check covers registration, the exact label, the handler, and the
    # singleton, rather than bypassing the menu via open_hub().
    menu_actions = [
        a for a in mw.form.menuTools.actions()
        if a.text() == hub_mod.MENU_LABEL
    ]
    result["menu_action_count"] = len(menu_actions)
    if len(menu_actions) != 1:
        report["ok"] = False
        done()
        return

    # Expected rows re-derived from the collection (newest id first) —
    # independent of hub.list_payload's own implementation.
    note_ids = sorted(
        col.find_notes(f'"note:{provisioning.ARTICLE_NOTE_TYPE}"'),
        reverse=True,
    )
    expected = []
    progress_before = {}
    for nid in note_ids:
        note = col.get_note(nid)
        expected.append(
            {
                "id": nid,
                "title": note["Title"] or "",
                "skills": [
                    f"{_HUB_SKILL_LABELS[m]} {_progress_pct(note, m)}%"
                    for m in MODES
                ],
            }
        )
        for m in MODES:
            progress_before[(nid, m)] = get_progress(note, m)

    # A leftover Hub from an earlier run/check must not mask the singleton.
    if hub_mod._hub is not None:
        try:
            hub_mod._hub.close()
        except Exception:
            pass

    menu_actions[0].trigger()          # opens the Hub on the list page
    hub = hub_mod._hub
    result["hub_opened"] = hub is not None
    if hub is None:
        report["ok"] = False
        done()
        return
    menu_actions[0].trigger()          # must raise, not duplicate
    result["singleton_same"] = hub_mod._hub is hub
    injected = None  # (nid, skill, value) written while on the practice page

    def snapshot() -> dict:
        return {
            (nid, m): get_progress(col.get_note(nid), m)
            for nid in note_ids
            for m in MODES
        }

    def finish(ok: bool) -> None:
        try:
            hub.close()
        except Exception:
            pass
        report["ok"] = ok and bool(result.get("singleton_same"))
        done()

    def probe_list(payload):
        try:
            d = json.loads(payload)
            result["list"] = d
            rows_ok = d["rows"] == [
                {"title": e["title"], "skills": e["skills"]} for e in expected
            ]
            ids_ok = d["ids"] == [e["id"] for e in expected]  # newest first
            title_ok = hub.windowTitle() == hub_mod.LIST_TITLE
            result["list_ok"] = rows_ok and ids_ok and title_ok
            if not (rows_ok and ids_ok and title_ok):
                finish(False)
                return
            # Enter practice by CLICKING the first row's reading entry —
            # exercises list.js -> pycmd -> bridge, not a Python shortcut.
            # Fire-and-forget: the click navigates the page (setHtml), which
            # would DROP a pending runJavaScript result callback — so the
            # next probe is scheduled from Python, not from the JS callback.
            hub.web.page().runJavaScript(
                "document.querySelector('.row .skill').click()"
            )
            after_delay(1500, lambda: _js(hub, _JS_HUB_PRACTICE, probe_practice))
        except Exception:
            result["list_err"] = traceback.format_exc()
            finish(False)

    def probe_practice(payload):
        nonlocal injected
        try:
            d = json.loads(payload)
            result["practice"] = d
            newest = expected[0]
            note = col.get_note(newest["id"])
            total = len(field_to_lines(note["Content"]))
            prog = min(get_progress(note, "reading"), total)
            from .practice_dialog import MODE_LABELS

            title = hub.windowTitle()
            # Opening the practice page must not write progress.
            open_now = snapshot()
            open_now_ok = open_now == progress_before
            ok = (
                d["back"]
                and d["backFirst"]            # back sits at the toolbar's left end
                and d["mode"] == "reading"
                and d["counter"] == f"{prog}/{total}"
                and d["rows"] == total
                and MODE_LABELS["reading"] in title
                and newest["title"] in title
                and open_now_ok
            )
            result["practice_ok"] = ok
            if not ok:
                finish(False)
                return
            # Simulate the extract-time progress write (the only write
            # path) for the article open in practice, so the return-to-list
            # refresh scenario is observable. Skip when already complete —
            # a monotonic extract would not advance either.
            cur = get_progress(note, "reading")
            if 0 < total and cur < total:
                _set_progress_raw(col, newest["id"], "reading", total)
                injected = (newest["id"], "reading", total)
                expected[0]["skills"][0] = "Reading 100%"
            # Return via the DOM back control (list.js contract: lsa:back).
            # Fire-and-forget again: lsa:back navigates (setHtml) and would
            # drop a pending result callback — schedule the probe from here.
            hub.web.page().runJavaScript(
                "document.getElementById('back').click()"
            )
            after_delay(1500, lambda: _js(hub, _JS_HUB_LIST, probe_back))
        except Exception:
            result["practice_err"] = traceback.format_exc()
            finish(False)

    def probe_back(payload):
        try:
            d = json.loads(payload)
            result["list_after_back"] = d
            # Refresh: the row touched during practice shows the new
            # percentage; every other row is unchanged.
            rows_ok = d["rows"] == [
                {"title": e["title"], "skills": e["skills"]} for e in expected
            ]
            title_ok = hub.windowTitle() == hub_mod.LIST_TITLE
            # Return-to-list must not write progress itself: state equals
            # the pre-navigation snapshot plus exactly the injected write.
            after = snapshot()
            expected_after = dict(progress_before)
            if injected:
                expected_after[(injected[0], injected[1])] = injected[2]
            back_now_ok = after == expected_after
            result["nav_ok"] = rows_ok and title_ok and back_now_ok
            result["injected"] = injected
            if not (rows_ok and title_ok and back_now_ok):
                finish(False)
                return
            # Empty state: render an empty payload (collection always has
            # the fixture, so this probes the template's empty branch).
            hub._set_html(list_html({"rows": []}))
            after_delay(1200, lambda: _js(hub, _JS_HUB_EMPTY, probe_empty))
        except Exception:
            result["back_err"] = traceback.format_exc()
            finish(False)

    def probe_empty(payload):
        try:
            d = json.loads(payload)
            result["empty"] = d
            finish(d["empty"] and d["rows"] == 0)
        except Exception:
            result["empty_err"] = traceback.format_exc()
            finish(False)

    after_delay(1300, lambda: _js(hub, _JS_HUB_LIST, probe_list))


def _progress_pct(note, skill: str) -> int:
    """Spec percentage rules, re-derived here (not via hub._progress_percent)
    so the selftest does not grade the helper with itself."""
    from .storage import field_to_lines

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
# dark learned-row style (change: dark-learned-row-style)
# ----------------------------------------------------------------------


def check_learned_style(mw, report, done) -> None:
    """dark-learned-row-style: learned rows carry a dark background band.

    Verifies the spec delta: dark tint perceivable in Listening mode (where a
    closed learned row shows no text), white primary text, full opacity +
    unchanged line-number color, toggle/play/selection/extract on a learned
    row, live darkening after an extract, and no tint without progress.
    """
    from .practice_dialog import open_dialog
    from aqt.qt import QApplication

    col = mw.col
    art = _ensure_long_article(col)
    result = report["detail"] = {}
    result["live_dark"] = {}
    DARK = "rgb(51, 51, 51)"  # #333 learned-row tint
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
        "learnedPrimaryColor: getComputedStyle(p).color,"
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
            # dark band perceivable with no text; unlearned rows untinted
            and d["learnedBg"] == DARK
            and d["unlearnedBg"] != DARK
            # primary text renders white on the dark band
            and d["learnedPrimaryColor"] == "rgb(255, 255, 255)"
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
            and d["learnedBg"] == DARK
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
            and d["bg"] == DARK
            and d["pf"] == "20/40"
        )
        result["live_dark"]["ok"] = d["ok"]
        result["live_dark"]["detail"] = d
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
        d["ok"] = d["learned"] == 0 and d["bg1"] != DARK and d["pf"] == "0/40"
        try:
            state["dlg_c"].close()
        except Exception:
            pass
        report["ok"] = all(
            result.get(k, {}).get("ok")
            for k in ("listening", "reading_band", "extract",
                      "live_dark", "no_progress")
        )
        done()

    open_listening()


def _keys_js(ks) -> str:
    """JS that dispatches synthetic key events on the page (the same
    KeyboardEvent pattern check_extract_all_modes uses for `a`)."""
    return "(function(){%s;return 'fired';})()" % "".join(
        "document.dispatchEvent(new KeyboardEvent('keydown',{key:%s,"
        "bubbles:true,cancelable:true}));" % json.dumps(k)
        for k in ks
    )


_JS_KBD_LIST = (
    "(function(){"
    "function ke(k){document.dispatchEvent(new KeyboardEvent('keydown',"
    "{key:k,bubbles:true,cancelable:true}));}"
    # keymap overlay toggles on and off without touching page state
    "ke('?'); var ovShow=!document.getElementById('keys').hidden;"
    "ke('?'); var ovHide=document.getElementById('keys').hidden;"
    # m opens the focused row's menu; a second m closes it again (toggle;
    # Escape is deliberately unbound — Anki's injected onEsc closes the
    # window, design D11)
    "ke('m'); var menuOpen=!!document.querySelector('.menu-pop:not([hidden])');"
    "ke('m');"
    "var menuClosed=!document.querySelector('.menu-pop:not([hidden])');"
    # skill column then rows: j must PRESERVE the skill column (spec)
    "ke('l');"
    "{jkeys}"
    "var rows=document.querySelectorAll('.row');"
    "var kr=document.querySelector('.krow');"
    "var midIdx=kr?Array.prototype.indexOf.call(rows,kr):-1;"
    "var ms=kr&&kr.querySelector('.skill.kskill');"
    "var midName=ms?ms.querySelector('.name').textContent:'';"
    # h wraps: index 1 -> 0 -> 3 (Writing)
    "ke('h'); ke('h');"
    "var ws=kr&&kr.querySelector('.skill.kskill');"
    "var wrapName=ws?ws.querySelector('.name').textContent:'';"
    # digit 4 = direct skill pick (Writing), same entry point as a click
    "ke('4');"
    "var fs=document.querySelector('.krow .skill.kskill');"
    "var finName=fs?fs.querySelector('.name').textContent:'';"
    "var open=fs?fs.dataset.open:'';"
    "var id=kr?+kr.dataset.id:0;"
    "return JSON.stringify({rows:rows.length, ovShow:ovShow, ovHide:ovHide,"
    "menuOpen:menuOpen, menuClosed:menuClosed,"
    "midIdx:midIdx, midName:midName, wrapName:wrapName, finName:finName,"
    "open:open, id:id});})()"
)

_JS_KBD_PRACTICE = (
    "(function(){"
    # first keyboard use materialises the caret; probe that it is a BAR
    # only — no character background, so it cannot be mistaken for a
    # selection band (user report on the caret-vs-selection confusion)
    "function ke(k){document.dispatchEvent(new KeyboardEvent('keydown',"
    "{key:k,bubbles:true,cancelable:true}));}"
    "ke('l');"
    "var cs=document.querySelector('.caret');"
    "var caretBg=cs?getComputedStyle(cs).backgroundColor:'<none>';"
    # vim parity: `v` starts collapsed on the CURSOR character (1 char,
    # no auto word pick); the second `v` cancels it
    "ke('v'); var vLen=getSelection().toString().length;"
    "ke('v'); var s2=getSelection();"
    "var vCancelled=(s2.rangeCount===0||s2.isCollapsed);"
    "return JSON.stringify({"
    "mode:(document.getElementById('mode-name')||{}).textContent,"
    "cursor:!!document.querySelector('.line.kcursor'),"
    "curline:(document.querySelector('.line.kcursor')||"
    "{dataset:{}}).dataset.line,"
    "counter:(document.getElementById('pf')||{}).textContent,"
    "rows:document.querySelectorAll('.line').length,"
    "caretBg:caretBg, vLen:vLen, vCancelled:vCancelled});})()"
)

_JS_KBD_SEL = (
    "JSON.stringify({collapsed:getSelection().isCollapsed,"
    "text:getSelection().toString()})"
)

_JS_KBD_JCANCEL = (
    "JSON.stringify({collapsed:getSelection().isCollapsed,"
    "curline:(document.querySelector('.line.kcursor')||"
    "{dataset:{}}).dataset.line})"
)

_JS_KBD_REVEAL = (
    "var r=document.querySelector('.line.kcursor');"
    "var src=r&&r.querySelector('.secondary.source');"
    "JSON.stringify({open:!!(r&&r.classList.contains('open')),"
    "src:src?getComputedStyle(src).display:'<none>',"
    "counter:document.getElementById('pf').textContent})"
)

_JS_KBD_BACK = (
    "JSON.stringify({"
    "rows:document.querySelectorAll('.row').length,"
    "titleRows:Array.from(document.querySelectorAll('.row')).map("
    "function(r){return r.querySelector('.title').textContent;}),"
    "pcts:Array.from(document.querySelectorAll('.row')).map(function(r){"
    "return Array.from(r.querySelectorAll('.skill')).map(function(s){"
    "return s.querySelector('.pct').textContent;});})})"
)


def check_keyboard_nav(mw, report, done) -> None:
    """add-vim-keyboard-navigation (specs: practice-hub -> List-page
    keyboard navigation / List-page keyboard row actions; practice-dialog
    -> Line cursor and keyboard movement / Keyboard text selection and
    extract / Keyboard line reveal and playback / Keyboard return and
    keymap help).

    Drives both Hub pages with synthetic key events: list overlay +
    row/skill cursor (column preservation, wrapping, direct digit) ->
    Enter into practice -> V visual selection reaching Python -> Esc
    cancel probe (design risk item: does Esc reach the page?) -> V+a
    extract through the unchanged pipeline -> Enter reveal -> q back with
    the refreshed percentage and no keypress progress writes.
    """
    from . import hub as hub_mod
    from .practice_dialog import MODES
    from .storage import field_to_lines
    from aqt.qt import QApplication

    col = mw.col
    art = _ensure_long_article(col)
    provisioning.provision(col)
    result = report["detail"] = {}

    # Deterministic cursor/extract line: earlier checks leave progress
    # behind on the shared fixture (e.g. writing 14 from extract rounds).
    for s in MODES:
        _set_progress_raw(col, art, s, 0)
    note = col.get_note(art)
    total = len(field_to_lines(note["Content"]))
    tr_lines = field_to_lines(note["Translation"])
    result["total"] = total

    # The exercised article's row position (newest first) — derived, not
    # hardcoded: earlier checks create more articles than this one.
    note_ids = sorted(
        col.find_notes(f'"note:{provisioning.ARTICLE_NOTE_TYPE}"'),
        reverse=True,
    )
    idx = note_ids.index(art)

    # A leftover Hub from an earlier check must not mask ours.
    if hub_mod._hub is not None:
        try:
            hub_mod._hub.close()
        except Exception:
            pass
    hub = hub_mod.open_hub(None)
    result["hub_opened"] = hub is not None
    if hub is None:
        report["ok"] = False
        done()
        return

    def finish(ok: bool) -> None:
        try:
            hub.close()
        except Exception:
            pass
        report["ok"] = ok
        done()

    def fail(stage: str, detail):
        result[stage] = detail
        finish(False)

    # -- Stage 1: list page keys ----------------------------------------

    def probe_list(payload):
        try:
            d = json.loads(payload)
            result["list"] = d
            ok = (
                d["rows"] >= 1
                and d["ovShow"] and d["ovHide"]          # overlay toggles
                and d["menuOpen"] and d["menuClosed"]    # m opens, Esc closes
                and d["midIdx"] == idx                   # j landed on art row
                and d["midName"] == "Speaking"           # skill column kept
                and d["wrapName"] == "Writing"           # h wraps 1->0->3
                and d["finName"] == "Writing"            # digit 4 direct
                and d["id"] == art
                and d["open"].endswith(":writing")
            )
            if not ok:
                fail("list_ok", False)
                return
            result["list_ok"] = True
            # Enter navigates (setHtml swaps the page and would drop a
            # pending result callback) — fire and probe from Python.
            hub.web.page().runJavaScript(_keys_js(["Enter"]))
            after_delay(1600, lambda: _js(hub, _JS_KBD_PRACTICE,
                                          probe_practice))
        except Exception:
            fail("list_err", traceback.format_exc())

    # -- Stage 2: practice page opened via keyboard ---------------------

    def probe_practice(payload):
        try:
            d = json.loads(payload)
            result["practice"] = d
            ok = (
                d["mode"] == "writing"
                and d["cursor"]
                and d["curline"] == "1"                 # cursor = progress+1
                and d["counter"] == f"0/{total}"
                and d["rows"] == total
                # caret is a bar, never a filled character (selection look)
                and d["caretBg"] == "rgba(0, 0, 0, 0)"
                # v = vim: one char at the cursor, second v cancels
                and d["vLen"] == 1
                and d["vCancelled"]
            )
            if not ok:
                fail("practice_ok", False)
                return
            result["practice_ok"] = True
            hub.web.page().runJavaScript(_keys_js(["V"]))
            after_delay(700, lambda: _js(hub, _JS_KBD_SEL, probe_visual))
        except Exception:
            fail("practice_err", traceback.format_exc())

    # -- Stage 3: V selects the whole cursor line into Python -----------

    def probe_visual(payload):
        try:
            d = json.loads(payload)
            result["visual_js"] = d
            sel = hub.selection
            result["visual_py"] = sel
            expected_text = tr_lines[0] if tr_lines else src_fallback(note)
            ok = (
                not d["collapsed"]
                and d["text"] == expected_text
                and isinstance(sel, dict)
                and sel.get("line") == 1
                and sel.get("start") == 0
                and sel.get("text") == expected_text
                and sel.get("end") == len(expected_text)
            )
            if not ok:
                fail("visual_ok", False)
                return
            result["visual_ok"] = True
            # Cancel probe: a SECOND `v` cancels the active visual
            # selection (Escape is deliberately unbound — Anki's injected
            # Escape->onEsc closes the window, design D11) -> collapsed
            # selection and a null selection on the Python side.
            hub.web.page().runJavaScript(_keys_js(["v"]))
            after_delay(700, lambda: _js(hub, _JS_KBD_SEL, probe_cancel))
        except Exception:
            fail("visual_err", traceback.format_exc())

    def probe_cancel(payload):
        try:
            d = json.loads(payload)
            result["cancel_js"] = d
            result["cancel_py"] = hub.selection
            ok = d["collapsed"] and hub.selection is None
            if not ok:
                fail("cancel_ok", False)
                return
            result["cancel_ok"] = True
            # Line movement must CANCEL an active visual selection (user
            # behavior: the single-line extract contract makes
            # whole-new-line re-selection surprising) — V then j ->
            # collapsed selection, cursor on line 2.
            hub.web.page().runJavaScript(_keys_js(["V", "j"]))
            after_delay(700, lambda: _js(hub, _JS_KBD_JCANCEL,
                                         probe_jcancel))
        except Exception:
            fail("cancel_err", traceback.format_exc())

    def probe_jcancel(payload):
        try:
            d = json.loads(payload)
            result["jcancel_js"] = d
            result["jcancel_py"] = hub.selection
            ok = (
                d["collapsed"]
                and d["curline"] == "2"
                and hub.selection is None
            )
            if not ok:
                fail("jcancel_ok", False)
                return
            result["jcancel_ok"] = True
            # Back to line 1 and extract with `a` — the unchanged pipeline.
            baseline = {
                id(w)
                for w in QApplication.topLevelWidgets()
                if "Add" in type(w).__name__ and w.isVisible()
            }
            hub.web.page().runJavaScript(_keys_js(["k", "V"]))
            after_delay(500, lambda: fire_extract(baseline))
        except Exception:
            fail("jcancel_err", traceback.format_exc())

    # -- Stage 4: V + a extract (writing skips the lookup: fast) --------

    def fire_extract(baseline):
        state["baseline"] = baseline
        hub.web.page().runJavaScript(_keys_js(["a"]))

        def probe_acancel(payload):
            # `a` CONSUMES the selection (D12): collapsed right after the
            # keypress — the extract itself still sees the full span
            # (Python captured it synchronously before the clear arrived).
            try:
                d = json.loads(payload)
                result["acancel_js"] = d
                result["acancel_ok"] = d["collapsed"]
            except Exception:
                result["acancel_ok"] = False
            after_delay(2300, verify_extract)

        after_delay(700, lambda: _js(hub, _JS_KBD_SEL, probe_acancel))

    def visible_adds(baseline):
        return {
            id(w)
            for w in QApplication.topLevelWidgets()
            if "Add" in type(w).__name__ and w.isVisible()
        } - baseline

    def verify_extract():
        new_add = visible_adds(state["baseline"])
        entry = {
            "add_opened": bool(new_add),
            "progress": get_progress(col.get_note(art), "writing"),
            "extract_log": list(getattr(hub, "extract_log", [])),
        }
        result["extract"] = entry
        ok = (
            bool(new_add)
            and entry["progress"] == 1                  # wrote line 1
            and "start:line=1" in " | ".join(entry["extract_log"])
            and not any("ERR:" in e for e in entry["extract_log"])
            and result.get("acancel_ok")                # selection consumed
        )
        if not ok:
            fail("extract_ok", False)
            return
        result["extract_ok"] = True
        if new_add:
            target = next(
                w for w in QApplication.topLevelWidgets() if id(w) in new_add
            )
            _close_add_dialog(target, after_extract)
        else:
            after_extract()

    # -- Stage 5: Enter reveal on the next line -------------------------

    def after_extract():
        hub.web.page().runJavaScript(_keys_js(["j", "Enter"]))
        after_delay(700, lambda: _js(hub, _JS_KBD_REVEAL, probe_reveal))

    def probe_reveal(payload):
        try:
            d = json.loads(payload)
            result["reveal"] = d
            ok = (
                d["open"]
                and d["src"] != "none"                  # writing: source shown
                and d["counter"] == f"1/{total}"        # reveal wrote nothing
            )
            if not ok:
                fail("reveal_ok", False)
                return
            result["reveal_ok"] = True
            state["progress_before_q"] = {
                s: get_progress(col.get_note(art), s) for s in MODES
            }
            hub.web.page().runJavaScript(_keys_js(["q"]))
            after_delay(1600, lambda: _js(hub, _JS_KBD_BACK, probe_back))
        except Exception:
            fail("reveal_err", traceback.format_exc())

    # -- Stage 6: q back to the list ------------------------------------

    def probe_back(payload):
        try:
            d = json.loads(payload)
            result["back"] = d
            after_q = {
                s: get_progress(col.get_note(art), s) for s in MODES
            }
            pct = f"{int(1 * 100.0 / total + 0.5)}%"    # 1 of total lines
            rows_ok = (
                d["rows"] >= 1
                and idx < len(d["pcts"])
                and d["titleRows"][idx] == (note["Title"] or "")
                and d["pcts"][idx][3] == pct            # Writing ring refreshed
            )
            ok = (
                rows_ok
                and hub.windowTitle() == hub_mod.LIST_TITLE
                # the q keypress itself wrote nothing
                and after_q == state["progress_before_q"]
            )
            if not ok:
                fail("back_ok", False)
                return
            result["back_ok"] = True
            finish(True)
        except Exception:
            fail("back_err", traceback.format_exc())

    state = {}
    after_delay(1400, lambda: _js(
        hub, _JS_KBD_LIST.replace("{jkeys}", "ke('j');" * idx), probe_list
    ))


def src_fallback(note) -> str:
    """First source line — only used when the fixture lacks translations."""
    from .storage import field_to_lines

    lines = field_to_lines(note["Content"])
    return lines[0] if lines else ""


CHECKS_EXTRA = [
    ("hub_list", check_hub_list),
    ("dialog_modes", check_dialog_modes),
    ("dialog_restore", check_dialog_restore),
    ("selection_capture", check_selection_capture),
    ("tts", check_tts),
    ("extract_all_modes", check_extract_all_modes),
    ("learned_style", check_learned_style),
    ("keyboard_nav", check_keyboard_nav),
]
