"""Youdao dictionary JSON API client (entries only).

Spec: practice-extract → Prefilled note content / Dictionary lookup failure
tolerance. Port of the reference app's ``youdao_dict_service.dart``, restricted
to the entries that feed the Back field. Never raises to the caller: network
failures, timeouts, non-200 responses and parse errors all yield ``[]``.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

API_URL = "https://dict.youdao.com/jsonapi"
TIMEOUT_SECONDS = 5.0
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


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
    """Flutter parity: 'UK /ɪˈfemərəl/ US /ɪˈfemərəl/' joined by spaces."""
    return " ".join(f"{region} /{text}/" for region, text in phonetics)


def lookup(word: str) -> LookupResult:
    """Look up ``word``; empty results on any failure (never raises)."""
    word = word.strip()
    if not word:
        return LookupResult((), ())
    try:
        url = f"{API_URL}?q={urllib.parse.quote(word)}"
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            if getattr(resp, "status", 200) != 200:
                return LookupResult((), ())
            data = json.loads(resp.read().decode("utf-8", "replace"))
    except Exception:
        # Network error / timeout / bad JSON — never interrupt extraction.
        return LookupResult((), ())
    if not isinstance(data, dict):
        return LookupResult((), ())
    return LookupResult(
        tuple(_parse_entries(data)), tuple(_parse_phonetics(data))
    )


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
