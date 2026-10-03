"""<br>-canonical line storage for article content fields.

Spec: article-storage → Line-based content storage.
Decision D3: write `<br>` as the canonical separator; parse tolerantly so
values written by the system and values rewritten by Anki's rich editor both
yield the correct line sequence.
"""

from __future__ import annotations

import html
import re

# Anki's rich editor expresses line breaks as <br>, <p>/</p> or <div>/</div>.
_BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
_BLOCK_CLOSE_RE = re.compile(r"</\s*(p|div)\s*>", re.IGNORECASE)
_BLOCK_OPEN_RE = re.compile(r"<(p|div)(\s[^>]*)?>", re.IGNORECASE)


def lines_to_field(lines: list[str]) -> str:
    """Serialize plain-text lines into the canonical field value.

    Each line is HTML-escaped; lines are joined with literal ``<br>``.
    """
    return "<br>".join(html.escape(line, quote=False) for line in lines)


def field_to_lines(value: str | None) -> list[str]:
    """Parse a field value into plain-text lines (tolerant parser).

    - ``<br>`` (canonical) is the primary separator; raw ``\\n`` also works
    - rich-editor artifacts (``<p>``/``<div>`` wrappers) are normalized
    - HTML entities are unescaped back to plain text

    Returns ``[]`` for empty/whitespace-only values.

    Round-trip evidence (spike 1.4, Anki 26.8.1): a real edit in Anki's
    Svelte editor — three lines typed with Enter — saves the field as
    ``'Alpha<br>Beta<br>Gamma'``, i.e. the editor normalizes exactly to this
    canonical form; no extra normalization was needed.
    """
    if value is None:
        return []
    if not value.strip():
        return []
    text = _BR_RE.sub("\n", value)
    text = _BLOCK_CLOSE_RE.sub("\n", text)
    text = _BLOCK_OPEN_RE.sub("", text)
    text = html.unescape(text).replace("\xa0", " ")
    return text.split("\n")
