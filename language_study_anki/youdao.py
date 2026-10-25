"""Youdao dictionary JSON API client (entries only).

Spec: practice-extract → Prefilled note content / Dictionary lookup failure
tolerance. Port of the reference app's ``youdao_dict_service.dart``, restricted
to the entries that feed the Back field. Never raises to the caller: network
failures, timeouts, non-200 responses and parse errors all yield ``[]``.
"""

from __future__ import annotations

import json
import os
import platform
import ssl
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

API_URL = "https://dict.youdao.com/jsonapi"
TIMEOUT_SECONDS = 5.0
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

# --- diagnostics -----------------------------------------------------------
# lookup() never raises, so failures used to disappear without a trace.
# Failed and empty lookups are now appended to a log file — successful ones
# are NOT logged, so the log only grows when something is actually wrong.
# Destination: the LSA_YOUDAO_LOG env var if set, else the Anki base dir
# (survives add-on redeploys), else the system temp dir. ``last_error``
# carries the reason of the most recent attempt ("" when dictionary entries
# were found) so the extract log can surface it too. Anything going wrong
# while logging is swallowed — diagnostics must never break a lookup.
LOG_FILENAME = "youdao-debug.log"
LOG_MAX_BYTES = 256 * 1024

last_error = ""
_log_lock = threading.Lock()
_header_written = False


@dataclass(frozen=True)
class DictEntry:
    pos: str
    tran: str


@dataclass(frozen=True)
class LookupResult:
    """Full lookup outcome: dictionary entries + phonetics (UK/US pairs)."""

    entries: tuple
    phonetics: tuple  # of (region, text)


def format_phonetics(phonetics) -> str:
    """One phonetic per line: 'UK /ɪˈfemərəl/<br>US /ɪˈfemərəl/' — the spec's
    `<br>`-separator rule for field values. Deliberate divergence from the
    reference app, which space-joined onto a single line."""
    return "<br>".join(f"{region} /{text}/" for region, text in phonetics)


def _clip(text: str, limit: int = 160) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _timestamp() -> str:
    now = time.time()
    ms = int(now % 1 * 1000)
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)) + f".{ms:03d}"


def _log_path() -> str:
    override = os.environ.get("LSA_YOUDAO_LOG")
    if override:
        return override
    try:
        from aqt import mw

        if mw is not None and getattr(mw, "pm", None) is not None:
            base = mw.pm.base
            if base:
                return os.path.join(base, LOG_FILENAME)
    except Exception:
        pass
    return os.path.join(tempfile.gettempdir(), "language-study-" + LOG_FILENAME)


def _record(query: str, outcome: str, started: float) -> None:
    """Append one lookup attempt to the diagnostics log; never raises."""
    global _header_written
    try:
        path = _log_path()
        elapsed = time.monotonic() - started
        line = f"{_timestamp()} | q={query!r} | {outcome} | {elapsed:.2f}s\n"
        with _log_lock:
            directory = os.path.dirname(path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            if os.path.exists(path) and os.path.getsize(path) >= LOG_MAX_BYTES:
                os.replace(path, path + ".1")  # keep one rotated file
                _header_written = False
            if not _header_written:
                header = (
                    f"==== {_timestamp()} session start"
                    f" | python={platform.python_version()}"
                    f" ssl={ssl.OPENSSL_VERSION}"
                    f" proxies={urllib.request.getproxies()}"
                    f" timeout={TIMEOUT_SECONDS}s ====\n"
                )
                with open(path, "a", encoding="utf-8") as fh:
                    fh.write(header)
                _header_written = True
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(line)
    except Exception:
        pass


def lookup(word: str) -> LookupResult:
    """Look up ``word``; empty results on any failure (never raises).

    The reason for an empty result is kept in ``last_error``; failures and
    empty results are appended to the diagnostics log (see ``_log_path``),
    successful lookups are not logged.
    """
    global last_error
    word = word.strip()
    if not word:
        return LookupResult((), ())
    last_error = ""
    started = time.monotonic()
    query = _clip(word)
    try:
        url = f"{API_URL}?q={urllib.parse.quote(word)}"
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            status = getattr(resp, "status", 200)
            if status != 200:
                last_error = f"http {status}"
                _record(query, f"FAIL {last_error}", started)
                return LookupResult((), ())
            raw = resp.read()
        data = json.loads(raw.decode("utf-8", "replace"))
    except Exception as exc:
        # Network error / timeout / bad JSON — never interrupt extraction.
        last_error = f"{type(exc).__name__}: {exc}"
        _record(query, f"FAIL {last_error}", started)
        return LookupResult((), ())
    if not isinstance(data, dict):
        last_error = "non-dict json response"
        _record(query, f"FAIL {last_error}", started)
        return LookupResult((), ())

    result = LookupResult(
        tuple(_parse_entries(data)), tuple(_parse_phonetics(data))
    )
    if not result.entries:
        # HTTP 200 but no dictionary fields: dict.youdao.com answers full
        # sentences without ec/expand_ec — record which fields came back.
        keys = ",".join(list(data)[:8])
        last_error = f"no dictionary fields (keys: {keys})"
        _record(query, f"empty {last_error}", started)
    return result


def _parse_phonetics(data: dict) -> list:
    """Port of the reference app's `_parsePhonetics`: `simple` first, then
    `ec`; UK and US phone fields."""
    result: list = []
    for source in (data.get("simple"), data.get("ec")):
        if result or not isinstance(source, dict):
            continue
        words = source.get("word")
        if not isinstance(words, list) or not words:
            continue
        w0 = words[0]
        if not isinstance(w0, dict):
            continue
        uk = w0.get("ukphone")
        us = w0.get("usphone")
        if isinstance(uk, str) and uk:
            result.append(("UK", uk))
        if isinstance(us, str) and us:
            result.append(("US", us))
    return result


def _parse_entries(data: dict) -> list[DictEntry]:
    # Prefer expand_ec (structured pos + transList).
    expand = data.get("expand_ec")
    if isinstance(expand, dict):
        words = expand.get("word")
        if isinstance(words, list):
            result: list[DictEntry] = []
            for w in words:
                if not isinstance(w, dict):
                    continue
                pos = w.get("pos") or ""
                trans_list = w.get("transList")
                if not isinstance(trans_list, list):
                    continue
                parts = [
                    str(t.get("trans"))
                    for t in trans_list
                    if isinstance(t, dict) and t.get("trans")
                ]
                if parts:
                    result.append(DictEntry(pos=str(pos), tran="；".join(parts)))
            if result:
                return result

    # Fallback: ec field ("adj. 短暂的" style strings).
    ec = data.get("ec")
    if not isinstance(ec, dict):
        return []
    words = ec.get("word")
    if not isinstance(words, list) or not words:
        return []
    first_word = words[0]
    if not isinstance(first_word, dict):
        return []
    trs = first_word.get("trs")
    if not isinstance(trs, list):
        return []

    entries: list[DictEntry] = []
    for tr in trs:
        if not isinstance(tr, dict):
            continue
        tr_array = tr.get("tr")
        if not isinstance(tr_array, list) or not tr_array:
            continue
        first = tr_array[0]
        if not isinstance(first, dict):
            continue
        l_obj = first.get("l")
        if not isinstance(l_obj, dict):
            continue
        items = l_obj.get("i")
        if not isinstance(items, list) or not items:
            continue
        text = str(items[0])
        dot = text.find(". ")
        if 0 < dot < 10:
            entries.append(DictEntry(pos=text[: dot + 1] + " ", tran=text[dot + 2 :]))
        else:
            entries.append(DictEntry(pos="", tran=text))
    return entries
