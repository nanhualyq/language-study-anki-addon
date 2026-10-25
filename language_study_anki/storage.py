"""<br>-canonical line storage for article content fields.

Spec: article-storage → Line-based content storage.
Decision D3 (write side): write ``<br>`` as the canonical separator.
Read side: parse the stored HTML STRUCTURALLY (spec delta, design D1/D2) —
a leaf block element yields exactly one line, a container/wrapper block
yields no line of its own, and ``<br>`` is a hard line break. Document-edge
empty lines are dropped; interior empty lines are preserved. A field that
begins or ends with a blank line is therefore not representable (recorded
BREAKING behavior of this change).

The extractor is a single streaming pass over stdlib ``html.parser``
events (no third-party dependency): text is data, never re-parsed, so
entity-escaped markup (``&lt;br&gt;``) can never become a separator, and
``script``/``style``/comment content never becomes article lines.
"""

from __future__ import annotations

import html
from html.parser import HTMLParser

# Block-level elements that carry document structure. A block that gains no
# block descendant (a leaf) contributes exactly one line; a block that
# contains blocks (a wrapper such as Anki's editor outer <div>) contributes
# no line of its own. Void elements (hr, img, ...) are deliberately absent:
# they never receive a close event, so they must never be pushed.
_BLOCKS = frozenset(
    {
        "address", "article", "aside", "blockquote", "caption", "dd",
        "details", "div", "dl", "dt", "fieldset", "figcaption", "figure",
        "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header",
        "li", "main", "nav", "ol", "p", "pre", "section", "summary",
        "table", "tbody", "td", "tfoot", "th", "thead", "tr", "ul",
    }
)

# Non-content subtrees: their text must never become article lines.
_SKIP_TAGS = frozenset({"script", "style"})


class _LineExtractor(HTMLParser):
    """Streaming HTML → line sequence (design D2/D3/D4 event rules).

    Frames on the stack are ``[tag, has_block_descendant, emitted_line]``.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)  # decode entities once, as data
        self.lines: list[str] = []
        self._buf: list[str] = []
        self._stack: list[list] = []
        self._skip_depth = 0

    # -- emit/flush primitives -------------------------------------------
    def _emit(self, line: str) -> None:
        self.lines.append(line)
        if self._stack:
            self._stack[-1][2] = True  # a line was emitted during top's span

    def _flush(self, *, force: bool = False) -> None:
        """Emit the buffered text as one line; ``force`` emits an empty line."""
        line = "".join(self._buf)
        self._buf.clear()
        if line or force:
            self._emit(line)

    def _close_block(self) -> None:
        """Pop the innermost block and apply the block-end rule."""
        _tag, has_descendant, emitted = self._stack.pop()
        if any(self._buf):
            self._flush()
        elif not has_descendant and not emitted:
            self._emit("")  # empty leaf paragraph IS a blank line
        # else: a wrapper's close, or a close after a <br> that already
        # ended the line — no line (this is what kills phantom tails).

    # -- parser events ----------------------------------------------------
    def handle_starttag(self, tag, attrs) -> None:  # noqa: N802 (HTMLParser API)
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "br":
            self._flush(force=True)  # hard break: an empty line here counts
            return
        if tag not in _BLOCKS:
            return  # inline/void elements never affect line boundaries
        # Implied close BEFORE marking/pushing (design D3).
        if self._stack and self._stack[-1][0] == "p":
            self._close_block()
        elif tag == "li" and self._stack and self._stack[-1][0] == "li":
            self._close_block()
        self._flush()  # buffered inline text before the block is its own line
        for frame in self._stack:
            frame[1] = True  # every open block gains a block descendant
        self._stack.append([tag, False, False])

    def handle_endtag(self, tag) -> None:  # noqa: N802 (HTMLParser API)
        if tag in _SKIP_TAGS:
            if self._skip_depth:
                self._skip_depth -= 1
            return
        if self._skip_depth or tag not in _BLOCKS:
            return
        for idx in range(len(self._stack) - 1, -1, -1):
            if self._stack[idx][0] == tag:
                # Close the match and any malformed frames nested above it.
                while len(self._stack) > idx:
                    self._close_block()
                return
        # Stray unmatched close tag: ignore (design D3).

    def handle_data(self, data) -> None:  # noqa: N802 (HTMLParser API)
        if self._skip_depth:
            return  # script/style/comment content never becomes a line
        data = data.replace("\r", "")  # CRLF/CR normalization (design D4)
        data = data.replace("\xa0", " ")  # nbsp → space, as before
        if not self._buf and not data.strip():
            return  # whitespace-only text between pasted tags
        parts = data.split("\n")
        self._buf.append(parts[0])
        for part in parts[1:]:
            self._flush(force=True)  # a raw \n in data is a hard break
            self._buf.append(part)

    # -- completion -------------------------------------------------------
    def finish_lines(self) -> list[str]:
        """Flush pending text, drop document-edge empty lines, return."""
        self.close()  # flushes any charref data the parser still buffers
        self._flush()  # remaining buffered text (no phantom when empty)
        while self.lines and not self.lines[-1].strip():
            self.lines.pop()
        while self.lines and not self.lines[0].strip():
            self.lines.pop(0)
        return self.lines


def lines_to_field(lines: list[str]) -> str:
    """Serialize plain-text lines into the canonical field value.

    Each line is HTML-escaped; lines are joined with literal ``<br>``.
    """
    return "<br>".join(html.escape(line, quote=False) for line in lines)


def field_to_lines(value: str | None) -> list[str]:
    """Parse a field value into plain-text lines (structural parser).

    Rules (spec delta: article-storage → Line-based content storage):

    - leaf block element (``<div>x</div>``, ``<p>x</p>`, ``<li>x</li>`` …)
      → exactly one line; a wrapper block (one containing blocks) → none
    - ``<br>`` and raw ``\\n`` inside data are hard line breaks
    - attributes and inline markup (``<b>``, ``<span>`` …) never affect
      boundaries; text is decoded exactly once, so ``&lt;br&gt;`` stays text
    - ``script``/``style``/comments, whitespace-only inter-tag text and
      ``\\r`` are normalized away
    - leading/trailing empty lines are dropped (edge artifacts); interior
      empty lines are preserved — a field may NOT begin or end with a
      representable blank line

    Returns ``[]`` for empty/whitespace-only values.
    """
    if value is None:
        return []
    if not value.strip():
        return []
    extractor = _LineExtractor()
    extractor.feed(value)
    return extractor.finish_lines()
