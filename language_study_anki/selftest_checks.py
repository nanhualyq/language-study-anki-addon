"""Self-test checks (development tooling). See selftest.py for the runner.

Each check has signature ``fn(mw, report, done)`` — must set
``report["ok"]``/``report["detail"]`` and call ``done()`` exactly once
(sync steps may call it immediately).
"""

from __future__ import annotations

import inspect
import traceback

from . import provisioning
from .selftest import after_delay
from .suspension import SUSPENDED_QUEUE, ensure_note_suspended


def _close_add_dialog(widget, on_closed=None) -> None:
    """Close an AddCards dialog AND answer its 'discard draft?' prompt.

    NewAddCards._close_if_user_wants_to_discard_changes pops a QMessageBox
    ("是否丢弃草稿" / "Discard draft?"); in automated runs nobody answers it,
    leaving modal residue that blocks later steps. ``on_closed`` fires only
    after the prompt is answered (or ruled out) — steps must defer ``done()``
    to it, otherwise the NEXT step races the teardown.
    """
    from aqt.qt import QApplication, QMessageBox, QTimer

    try:
        widget.close()
    except Exception:
        pass
    state = {"n": 0}

    def _notify() -> None:
        if on_closed is not None:
            on_closed()

    def pump() -> None:
        state["n"] += 1
        for w in QApplication.topLevelWidgets():
            if isinstance(w, QMessageBox) and w.isVisible():
                btns = w.buttons()
                chosen = None
                for b in btns:
                    t = b.text().lower()
                    if any(k in t for k in ("discard", "丢弃", "放弃", "捨弃", "不保存")):
                        chosen = b
                        break
                if chosen is None and len(btns) >= 2:
                    keep = [
                        b
                        for b in btns
                        if not any(
                            k in b.text().lower()
                            for k in ("cancel", "取消", "keep", "保留")
                        )
                    ]
                    chosen = keep[0] if keep else btns[0]
                if chosen is not None:
                    chosen.click()
                else:
                    w.accept()
                QTimer.singleShot(250, _notify)
                return
        if state["n"] < 10:
            QTimer.singleShot(300, pump)
        else:
            _notify()  # no prompt appeared (dialog had no draft)

    QTimer.singleShot(250, pump)


def _names_count(col) -> dict:
    counts: dict = {}
    for model in col.models.all():
        counts[model["name"]] = counts.get(model["name"], 0) + 1
    return counts


# ---------------------------------------------------------------- checks


def check_provision_and_adopt(mw, report, done) -> None:
    """Tasks 2.1 + 2.2: idempotent provisioning; existing types adopted."""
    try:
        col = mw.col
        mm = col.models

        # Plant a pre-existing @EnSpeak with a marker field (fresh bases only)
        # so provisioning must ADOPT it instead of duplicating.
        decoy_planted = False
        if mm.by_name("@EnSpeak") is None:
            model = mm.new("@EnSpeak")
            # Full extract field set + a marker: adoption must preserve the
            # marker, and the extract flow needs Front/Back/Title/Url.
            for field in provisioning.EXTRACT_FIELD_NAMES + ["AdoptedMarker"]:
                mm.add_field(model, mm.new_field(field))
            tmpl = mm.new_template("Card 1")
            tmpl["qfmt"] = "{{Front}}"
            tmpl["afmt"] = "{{Front}}"
            mm.add_template(model, tmpl)
            mm.add(model)
            decoy_planted = True

        p1 = provisioning.provision(col)
        p2 = provisioning.provision(col)

        counts = _names_count(col)
        targets = (
            [provisioning.ARTICLE_NOTE_TYPE]
            + provisioning.EXTRACT_NOTE_TYPES
        )
        duplicates = {n: counts.get(n, 0) for n in targets if counts.get(n, 0) != 1}

        adopted = mm.by_name("@EnSpeak")
        has_marker = any(
            f["name"] == "AdoptedMarker" for f in adopted["flds"]
        ) or not decoy_planted  # marker absent only OK if it pre-existed before us

        same_ids = (
            p1["article_notetype"]["id"] == p2["article_notetype"]["id"]
            and p1["article_deck_id"] == p2["article_deck_id"]
            and p1["extract_deck_id"] == p2["extract_deck_id"]
            and all(
                p1["extract_notetypes"][n]["id"] == p2["extract_notetypes"][n]["id"]
                for n in provisioning.EXTRACT_NOTE_TYPES
            )
        )
        article_fields = [f["name"] for f in p1["article_notetype"]["flds"]]
        fields_ok = article_fields == provisioning.ARTICLE_FIELDS
        sort_ok = p1["article_notetype"]["sortf"] == 0

        report["ok"] = not duplicates and has_marker and same_ids and fields_ok and sort_ok
        report["detail"] = {
            "decoy_planted": decoy_planted,
            "duplicates": duplicates,
            "adopted_marker_field": has_marker,
            "stable_across_runs": same_ids,
            "article_fields": article_fields,
            "sortf_is_title": sort_ok,
            "article_deck_id": p1["article_deck_id"],
            "extract_deck_id": p1["extract_deck_id"],
        }
    except Exception:
        report["detail"] = traceback.format_exc()
    done()


def check_article_suspension(mw, report, done) -> None:
    """Task 2.3: cards suspended at creation (Add-dialog hook) and after a
    note edit; direct-API creation is repaired by the ensure helper."""
    result = report["detail"] = {}
    try:
        from aqt import dialogs

        col = mw.col
        prov = provisioning.provision(col)
        model = prov["article_notetype"]

        # (a) direct API creation → ensure helper repairs immediately
        note = col.new_note(model)
        note["Title"] = "LSA selftest article"
        note["Content"] = "Alpha<br>Beta"
        col.add_note(note, prov["article_deck_id"])
        card_ids = col.card_ids_of_note(note.id)
        result["queues_after_direct_add"] = [col.get_card(c).queue for c in card_ids]
        ensure_note_suspended(note)
        result["queues_after_ensure"] = [
            col.get_card(c).queue for c in col.card_ids_of_note(note.id)
        ]
        note["Title"] = "LSA selftest article v2"
        note.flush()
        result["queues_after_edit"] = [
            col.get_card(c).queue for c in col.card_ids_of_note(note.id)
        ]

        # (b) creation via the Add dialog → add_cards_did_add_note hook fires
        # NOTE: set_note copies into the dialog's own note clone — our object
        # never receives an id, so verification queries by unique title.
        import time as _time

        unique_title = f"LSA via add dialog {int(_time.time() * 1000)}"
        note2 = col.new_note(model)
        note2["Title"] = unique_title
        note2["Content"] = "Gamma<br>Delta"
        dlg = dialogs.open("AddCards", mw)
        _set_note_any(dlg, note2, prov["article_deck_id"])
        btn_attr, btn = _find_add_button(dlg)
        result["add_button"] = btn_attr
        if btn is None:
            report["ok"] = False
            result["fail"] = "no add button"
            done()
            return

        def after_add() -> None:
            try:
                found = col.find_notes(f'Title:"{unique_title}"')
                real_id = next(iter(found)) if found else None
                added = real_id is not None
                ids2 = col.card_ids_of_note(real_id) if added else []
                queues2 = [col.get_card(c).queue for c in ids2]
                decks2 = [col.get_card(c).did for c in ids2]
                result["dialog_note_added"] = added
                result["dialog_card_queues"] = queues2
                result["dialog_card_decks"] = decks2
                report["ok"] = (
                    all(q == SUSPENDED_QUEUE for q in result["queues_after_ensure"])
                    and added
                    and bool(ids2)
                    and all(q == SUSPENDED_QUEUE for q in queues2)
                    and decks2 == [prov["article_deck_id"]]
                )
            except Exception:
                report["ok"] = False
                result["verify_error"] = traceback.format_exc()
            # Close only AFTER the discard prompt is answered, else the next
            # step races this teardown (evidence: editor.note stayed None).
            _close_add_dialog(dlg, done)

        # The editor loads asynchronously — wait until it holds OUR note so
        # the Add click is not swallowed (same lesson as the set_note spike).
        tries = {"n": 0}

        def click_when_ready() -> None:
            ed = getattr(getattr(dlg, "editor", None), "note", None)
            ed_front = ed.fields[0] if (ed is not None and ed.fields) else None
            state_ok = ed_front == unique_title
            result.setdefault("ready_timeline", []).append(
                [getattr(ed, "id", None), str(ed_front)[:30]]
            )
            if state_ok:
                btn.click()
                after_delay(2500, after_add)
                return
            tries["n"] += 1
            if tries["n"] > 30:
                result["fail"] = "editor never held our article note"
                report["ok"] = False
                try:
                    dlg.close()
                except Exception:
                    pass
                done()
                return
            after_delay(200, click_when_ready)

        after_delay(300, click_when_ready)
        return
    except Exception:
        report["ok"] = False
        result["error"] = traceback.format_exc()
        done()


def _set_note_any(dlg, note, deck_id: int) -> str:
    """Call set_note with whichever signature this Anki build uses."""
    attempts = [
        ("deck_id kw", lambda: dlg.set_note(note, deck_id=deck_id)),
        ("positional", lambda: dlg.set_note(note, deck_id)),
        ("note only", lambda: dlg.set_note(note)),
    ]
    errors = []
    for label, call in attempts:
        try:
            call()
            return label
        except TypeError as e:
            errors.append(f"{label}: {e}")
    raise RuntimeError("set_note failed: " + " | ".join(errors))


def _find_add_button(dlg):
    for attr in dir(dlg):
        if "add" not in attr.lower():
            continue
        obj = getattr(dlg, attr, None)
        if callable(getattr(obj, "click", None)):
            return attr, obj
    return None, None


def check_add_dialog_set_note(mw, report, done) -> None:
    """Task 1.2: NewAddCards.set_note prefills; confirm adds, cancel doesn't."""
    result = report["detail"] = {}
    try:
        from aqt import dialogs

        col = mw.col
        prov = provisioning.provision(col)
        model = prov["extract_notetypes"]["@Basic"]

        note = col.new_note(model)
        import time as _time

        unique = f"lsa-add-{int(_time.time() * 1000)}"
        note["Front"] = unique
        note["Back"] = "back text"
        note["Title"] = "title text"
        note["Url"] = "https://example.com"

        dlg = dialogs.open("AddCards", mw)
        result["signature"] = str(inspect.signature(dlg.set_note))
        result["set_note_call"] = _set_note_any(dlg, note, prov["extract_deck_id"])
        result["unique_front"] = note.fields[0]

        btn_attr, btn = _find_add_button(dlg)
        result["add_button"] = btn_attr
        if btn is None:
            result["candidates"] = [a for a in dir(dlg) if "add" in a.lower()]
            report["ok"] = False
            done()
            return

        # The editor loads asynchronously — poll until it holds OUR note,
        # so the Add click is not swallowed.
        ready = {"tries": 0, "timeline": []}

        def poll_ready() -> None:
            editor = getattr(dlg, "editor", None)
            ed_note = getattr(editor, "note", None)
            ed_front = ed_note.fields[0] if (ed_note is not None and ed_note.fields) else None
            ready["timeline"].append([getattr(ed_note, "id", None), str(ed_front)[:30]])
            if ed_front == note.fields[0]:
                result["editor_ready_after_tries"] = ready["tries"]
                btn.click()
                after_delay(600, lambda: poll_added(0))
                return
            ready["tries"] += 1
            if ready["tries"] > 30:
                result["editor_note_timeline"] = ready["timeline"][:10]
                result["fail"] = "editor never held our note"
                report["ok"] = False
                _close_add_dialog(dlg, done)
                return
            after_delay(200, poll_ready)

        def poll_added(tries: int) -> None:
            try:
                ids = col.find_notes(f'Front:"{note.fields[0]}"')
                if ids and tries < 20:
                    real_id = next(iter(ids))
                    real_note = col.get_note(real_id)
                    card_decks = [
                        col.get_card(c).did for c in col.card_ids_of_note(real_id)
                    ]
                    result["note_added"] = True
                    result["card_deck_ids"] = card_decks
                    result["expected_deck"] = prov["extract_deck_id"]
                    result["our_note_id"] = note.id
                    result["editor_note_id"] = getattr(
                        getattr(dlg, "editor", None), "note", None
                    ) and getattr(dlg.editor.note, "id", None)

                    # Cancel path: prefilled second note, close → not added.
                    note2 = col.new_note(model)
                    note2["Front"] = f"cancel path {note.fields[0]}"
                    _set_note_any(dlg, note2, prov["extract_deck_id"])
                    result["cancel_id"] = note2.id
                    result["cancel_in_collection"] = len(
                        col.find_notes(f'Front:"{note2.fields[0]}"')
                    )
                    report["ok"] = (
                        card_decks == [prov["extract_deck_id"]]
                        and note2.id in (None, 0)
                        and result["cancel_in_collection"] == 0
                        and str(real_note.fields[0]) == note.fields[0]
                    )
                    _close_add_dialog(dlg, done)
                    return
                if tries >= 20:
                    result["fail"] = "note never appeared after add click"
                    result["note_added"] = False
                    report["ok"] = False
                    _close_add_dialog(dlg, done)
                    return
            except Exception:
                report["ok"] = False
                result["verify_error"] = traceback.format_exc()
                _close_add_dialog(dlg, done)
                return
            after_delay(300, lambda: poll_added(tries + 1))

        after_delay(300, poll_ready)
    except Exception:
        report["ok"] = False
        result["error"] = traceback.format_exc()
        done()


def check_database_hygiene(mw, report, done) -> None:
    """Task 1.5: Check Database / empty-cards report stays clean for articles."""
    result = report["detail"] = {}
    try:
        col = mw.col
        result["col_check_attrs"] = [
            a for a in dir(col) if any(k in a.lower() for k in ("integrity", "check", "repair"))
        ]
        result["backend_check_attrs"] = [
            a for a in dir(col._backend)
            if any(k in a.lower() for k in ("integrity", "check", "empty"))
        ]

        report_text = None
        for obj, name in ((col, "fix_integrity"), (col._backend, "check_database")):
            fn = getattr(obj, name, None)
            if fn is None:
                continue
            try:
                report_text = fn()
                result["used"] = f"{type(obj).__name__}.{name}"
                break
            except Exception as e:
                result[f"{name}_error"] = str(e)
        result["report"] = str(report_text)[:4000] if report_text is not None else None

        # Empty-cards check: no article cards may be flagged.
        result["empty_fn"] = None
        empty_ids = []
        backend_empty = getattr(col._backend, "get_empty_cards", None)
        if backend_empty is not None:
            result["empty_fn"] = "_backend.get_empty_cards"
            try:
                empty_ids = list(backend_empty())
            except Exception as e:
                result["empty_error"] = str(e)
        result["empty_card_count"] = len(empty_ids)

        article_notes = col.find_notes(f'"note:{provisioning.ARTICLE_NOTE_TYPE}"')
        article_cards = []
        for nid in article_notes:
            article_cards.extend(col.card_ids_of_note(nid))
        flagged = sorted(set(article_cards) & set(empty_ids))
        result["article_cards_flagged_as_empty"] = flagged

        report["ok"] = report_text is not None and not flagged
    except Exception:
        report["ok"] = False
        result["error"] = traceback.format_exc()
    done()


CHECKS = [
    ("provision_and_adopt", check_provision_and_adopt),
    ("article_suspension", check_article_suspension),
    ("add_dialog_set_note", check_add_dialog_set_note),
    # editor_roundtrip retired from the automated suite: the Svelte editor
    # refuses synthetic activation (evidence: activate→ce=null,
    # rich-inserted:false). Task 1.4 was verified by a REAL manual edit —
    # the editor saved 'Alpha<br>Beta<br>Gamma' (recorded in tasks.md).
    ("database_hygiene", check_database_hygiene),
]
