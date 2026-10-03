"""Extraction flow: selection → prefilled Add dialog (spec: practice-extract).

Ports the reference app's per-mode extract behavior without AnkiConnect:

  reading   @Basic      Front=source ctx + <mark>   Back=youdao/translation
  writing   @Basic      Front=TRANSLATION ctx+<mark> Back=source line (no lookup)
  listening @EnListen   Front=source ctx, sel→???    Back=selected  Phone=phonetics
  speaking  @EnSpeak    Front=source ctx + <mark>    Back=selected  Phone=phonetics

The extract-time progress write is the ONLY progress write path (D8).
"""

from __future__ import annotations

import traceback

from .field_builder import build_front, resolve_back
from .progress import set_progress_at_least
from .provisioning import MODE_NOTETYPE, provision

_AUDIO_MODES = ("listening", "speaking")


def _log(dialog, msg: str) -> None:
    log = getattr(dialog, "extract_log", None)
    if log is None:
        log = dialog.extract_log = []
    log.append(msg)


def run_extract(dialog) -> None:
    """Ctrl+E handler. No selection → nothing happens (spec scenario)."""
    sel = dialog.selection
    if not sel:
        _log(dialog, "noop:no-selection")
        return
    _log(dialog, f"start:line={sel.get('line')} text={str(sel.get('text'))[:30]!r}")
    try:
        _start(dialog, sel)
    except Exception:
        _log(dialog, "ERR:_start " + traceback.format_exc())
        print("language_study_anki: extract failed:\n" + traceback.format_exc())


def _start(dialog, sel: dict) -> None:
    from aqt import mw

    if dialog.mode == "writing" and dialog._translations:
        # Flutter parity: writing performs no dictionary lookup.
        _log(dialog, "lookup:skipped(writing)")
        try:
            _open_add_dialog(dialog, sel, None)
            _log(dialog, "done")
        except Exception:
            _log(dialog, "ERR:finalize " + traceback.format_exc())
        return
    mw.taskman.run_in_background(
        lambda: _lookup(sel["text"]),
        lambda result: _on_entries(dialog, sel, result),
    )


def _lookup(text: str):
    from . import youdao

    try:
        return youdao.lookup(text)
    except Exception:
        return youdao.LookupResult((), ())  # never interrupt extraction


def _on_entries(dialog, sel: dict, result_or_future) -> None:
    try:
        from . import youdao

        result = result_or_future
        if hasattr(result, "result"):
            result = result.result()
        if not isinstance(result, youdao.LookupResult):
            result = youdao.LookupResult((), ())
        _log(dialog, f"lookup:{len(result.entries)} entries phon:{len(result.phonetics)}")
        _open_add_dialog(dialog, sel, result)
        _log(dialog, "done")
    except Exception:
        _log(dialog, "ERR:finalize " + traceback.format_exc())
        print("language_study_anki: extract finalize failed:\n" + traceback.format_exc())


def _open_add_dialog(dialog, sel: dict, result) -> None:
    from aqt import dialogs, mw

    col = mw.col
    article = dialog._article
    mode = dialog.mode
    line_no = int(sel["line"])
    start = int(sel["start"])
    end = int(sel["end"])
    lines = dialog._lines
    translations = dialog._translations

    entries = list(result.entries) if result is not None else []
    phone = ""
    if result is not None and mode in _AUDIO_MODES:
        from . import youdao

        phone = youdao.format_phonetics(result.phonetics)

    if mode == "writing" and translations:
        if not 1 <= line_no <= len(translations):
            raise ValueError(f"translation line {line_no} out of range")
        front = build_front(translations, line_no, start, end)
        back = lines[line_no - 1] if 1 <= line_no <= len(lines) else ""
        kinds = "front:translation back:source-line highlight:mark"
    else:
        highlight = "???" if mode == "listening" else ""
        front = build_front(lines, line_no, start, end, highlight_replacement=highlight)
        if mode in _AUDIO_MODES:
            back = sel["text"]
            kinds = "back:selection"
        else:
            back = resolve_back(entries, translations, line_no)
            kinds = "back:youdao" if entries else "back:fallback"
        kinds = (
            "front:source highlight:" + ("???" if mode == "listening" else "mark")
            + " " + kinds
        )
    _log(dialog, f"fields {kinds} phone:{len(phone)}")

    prov = provision(col)
    model = prov["extract_notetypes"][MODE_NOTETYPE[mode]]
    note = col.new_note(model)
    _log(dialog, f"note_type:{note.note_type()['name']}")

    field_values = [
        ("Front", front),
        ("Back", back),
        ("Title", article["Title"]),
        ("Url", article["Url"] or ""),
    ]
    if mode in _AUDIO_MODES:
        field_values.append(("Phone", phone))
    # Set only fields that exist (adopted foreign types may still lack one —
    # provisioning repairs them, this is the belt-and-braces layer).
    for fname, value in field_values:
        try:
            note[fname] = value
        except KeyError:
            _log(dialog, f"WARN:field-missing:{fname}")

    add_dlg = dialogs.open("AddCards", mw)
    try:
        add_dlg.set_note(note, deck_id=prov["extract_deck_id"])
    except TypeError:
        add_dlg.set_note(note, prov["extract_deck_id"])

    # Progress: extract-time write — the only write path (D8 / spec).
    set_progress_at_least(article, mode, line_no)
    _log(dialog, f"progress:{mode}>={line_no}")
    # Reflect the new progress immediately in the open practice dialog.
    try:
        dialog.web.page().runJavaScript(
            f"window.markLearnedUpTo && window.markLearnedUpTo({line_no})"
        )
    except Exception:
        pass
