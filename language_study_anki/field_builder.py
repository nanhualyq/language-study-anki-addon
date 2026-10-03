"""Extraction field construction.

Spec: practice-extract → Prefilled note content / Dictionary fallback.
Port of the reference app's ``anki_field_builder.dart`` (context + <mark> +
hidden timestamp) plus Back-field resolution (dictionary → translation line →
empty).
"""

from __future__ import annotations

import html
import time

CONTEXT_LINES = 3


def build_front(
    lines: list[str],
    line_number: int,
    start: int,
    end: int,
    *,
    highlight_replacement: str = "",
    timestamp_ms: int | None = None,
) -> str:
    """Build the Front field for a selection on ``line_number`` (1-based).

    Layout: up to 3 context lines (each ``<br>``-terminated) + the selected
    line with ``[start:end]`` wrapped in ``<mark>`` (or replaced by
    ``highlight_replacement``) + a hidden timestamp span keeping the field
    content unique (defeats duplicate detection).
    """
    if not 1 <= line_number <= len(lines):
        raise IndexError(f"line {line_number} out of range ({len(lines)} lines)")
    line = lines[line_number - 1]
    if not 0 <= start <= end <= len(line):
        raise IndexError("selection offsets out of line bounds")

    current = line_number - 1
    context_start = max(0, current - CONTEXT_LINES)
    parts = [
        html.escape(lines[i], quote=False) + "<br>"
        for i in range(context_start, current)
    ]

    selected = line[start:end] if not highlight_replacement else highlight_replacement
    parts.append(
        html.escape(line[:start], quote=False)
        + "<mark>"
        + html.escape(selected, quote=False)
        + "</mark>"
        + html.escape(line[end:], quote=False)
    )

    ts = int(time.time() * 1000) if timestamp_ms is None else int(timestamp_ms)
    parts.append(f'<span style="display:none">{ts}</span>')
    return "".join(parts)


def format_back(entries) -> str:
    """Format dictionary entries as the Back field (``pos tran`` joined by ``<br>``)."""
    if not entries:
        return ""
    return "<br>".join(f"{e.pos} {e.tran}" for e in entries)


def resolve_back(youdao_entries, translation_lines: list[str], line_number: int) -> str:
    """Dictionary entries → same-index translation line → empty."""
    if youdao_entries:
        return format_back(youdao_entries)
    idx = line_number - 1
    if 0 <= idx < len(translation_lines):
        # Plain text from the parser; escape so it renders safely as HTML.
        return html.escape(translation_lines[idx], quote=False)
    return ""
