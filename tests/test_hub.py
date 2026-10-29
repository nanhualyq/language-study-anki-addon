"""Unit tests for Hub list-page helpers.

Change: add-article-list-hub (spec: practice-hub → Article list page).

Covers the `_progress_percent` helper moved out of the deleted
browser_menu.py (same edge cases as before) plus the new list payload:
row ordering (newest first), per-skill percentages, and the empty state.

Zero-dependency style like the rest of tests/: `aqt` is not installed, so the
package is imported FIRST (its init() skips Anki hook registration when aqt is
absent), then a minimal `aqt.qt` stub is installed so `hub` imports cleanly.
"""

import json
import sys
import types
import unittest

import language_study_anki  # noqa: F401  (init() must run before the stub)


def _stub_aqt_qt() -> None:
    if "aqt" in sys.modules:
        return
    aqt = types.ModuleType("aqt")
    qt = types.ModuleType("aqt.qt")
    qt.QDialog = type("QDialog", (), {})
    qt.QVBoxLayout = type("QVBoxLayout", (), {})

    class _WindowType:  # minimal Qt.WindowType for the window-flag hints
        WindowMinimizeButtonHint = 0x10000000
        WindowMaximizeButtonHint = 0x01000000

    qt.Qt = types.SimpleNamespace(WindowType=_WindowType)
    aqt.qt = qt
    sys.modules["aqt"] = aqt
    sys.modules["aqt.qt"] = qt


_stub_aqt_qt()

from language_study_anki.hub import (  # noqa: E402
    _progress_percent,
    list_html,
    list_payload,
)
from language_study_anki.provisioning import ARTICLE_NOTE_TYPE  # noqa: E402

MODES = ("reading", "speaking", "listening", "writing")


def content_of(n: int) -> str:
    """Article Content field with n source lines (<br> separator)."""
    return "<br>".join(f"Source line {i}" for i in range(1, n + 1))


class FakeNote:
    def __init__(self, content="", note_type_name=ARTICLE_NOTE_TYPE, **fields):
        self.fields = {"Content": content}
        self.fields.update(fields)
        self._nt_name = note_type_name

    def __getitem__(self, key):
        return self.fields[key]

    def note_type(self):
        return {"name": self._nt_name}


class FakeCol:
    def __init__(self, notes, order=None):
        self.notes = notes
        # find_notes order is whatever the collection returns; the payload
        # must re-sort newest-first regardless.
        self.order = list(order) if order is not None else list(notes)

    def find_notes(self, query):
        assert ARTICLE_NOTE_TYPE in query, query
        return list(self.order)

    def get_note(self, nid):
        return self.notes[nid]


class ProgressPercentTests(unittest.TestCase):
    def test_exact_25_percent(self):
        note = FakeNote(content=content_of(40), ProgReading="10")
        self.assertEqual(_progress_percent(note, "reading"), 25)

    def test_zero_when_no_progress(self):
        note = FakeNote(content=content_of(40))
        self.assertEqual(_progress_percent(note, "reading"), 0)

    def test_zero_when_content_empty(self):
        note = FakeNote(content="", ProgReading="5")
        self.assertEqual(_progress_percent(note, "reading"), 0)

    def test_clamped_when_progress_past_line_count(self):
        note = FakeNote(content=content_of(40), ProgWriting="999")
        self.assertEqual(_progress_percent(note, "writing"), 100)

    def test_zero_for_garbage_progress(self):
        note = FakeNote(content=content_of(40), ProgSpeaking="abc")
        self.assertEqual(_progress_percent(note, "speaking"), 0)

    def test_zero_for_negative_progress(self):
        note = FakeNote(content=content_of(40), ProgListening="-3")
        self.assertEqual(_progress_percent(note, "listening"), 0)

    def test_half_up_rounding(self):
        # 1/8 = 12.5 → 13; 3/8 = 37.5 → 38 (deterministic half-up)
        self.assertEqual(
            _progress_percent(FakeNote(content_of(8), ProgReading="1"), "reading"),
            13,
        )
        self.assertEqual(
            _progress_percent(FakeNote(content_of(8), ProgReading="3"), "reading"),
            38,
        )

    def test_missing_content_field_is_zero(self):
        note = FakeNote(content=None, ProgReading="4")
        self.assertEqual(_progress_percent(note, "reading"), 0)

    def test_percent_uses_structural_line_count_for_edited_article(self):
        # Anki's rich editor wraps an edited article in an outer <div> with
        # one <div> per line (captured live: 56 lines, ProgReading 54).
        # The parser must not count the wrapper's closing tags as trailing
        # lines: 54/56 -> 96%, not the phantom-inflated 54/58 -> 93%.
        body = "".join(f"<div>Source line {i}</div>" for i in range(1, 57))
        content = f"<div>{body}</div>"
        note = FakeNote(content=content, ProgReading="54")
        self.assertEqual(_progress_percent(note, "reading"), 96)


class ListPayloadTests(unittest.TestCase):
    def test_rows_newest_first(self):
        notes = {
            11: FakeNote(content=content_of(40), Title="Old"),
            22: FakeNote(content=content_of(40), Title="New"),
            17: FakeNote(content=content_of(40), Title="Mid"),
        }
        # Collection returns an arbitrary order; payload sorts id-descending.
        col = FakeCol(notes, order=[17, 11, 22])
        rows = list_payload(col)["rows"]
        self.assertEqual([r["id"] for r in rows], [22, 17, 11])
        self.assertEqual([r["title"] for r in rows], ["New", "Mid", "Old"])

    def test_row_percentages_match_spec_scenario(self):
        # 40 lines, ProgReading 10 → 25%; ProgWriting 0 → 0%.
        note = FakeNote(
            content=content_of(40), Title="A", ProgReading="10", ProgWriting="0"
        )
        rows = list_payload(FakeCol({1: note}, order=[1]))["rows"]
        self.assertEqual(len(rows), 1)
        pcts = rows[0]["pcts"]
        self.assertEqual(list(pcts), list(MODES))  # reading/speaking/listening/writing
        self.assertEqual(pcts["reading"], 25)
        self.assertEqual(pcts["writing"], 0)
        self.assertEqual(pcts["speaking"], 0)
        self.assertEqual(pcts["listening"], 0)

    def test_progress_beyond_content_is_100(self):
        note = FakeNote(content=content_of(10), Title="A", ProgListening="99")
        rows = list_payload(FakeCol({1: note}, order=[1]))["rows"]
        self.assertEqual(rows[0]["pcts"]["listening"], 100)

    def test_empty_content_is_zero_everywhere(self):
        note = FakeNote(content="", Title="A", ProgReading="7")
        rows = list_payload(FakeCol({1: note}, order=[1]))["rows"]
        self.assertTrue(all(v == 0 for v in rows[0]["pcts"].values()))

    def test_empty_collection_yields_no_rows(self):
        self.assertEqual(list_payload(FakeCol({}, order=[])), {"rows": []})

    def test_missing_title_field_is_empty_string(self):
        note = FakeNote(content=content_of(4))  # no Title key at all
        rows = list_payload(FakeCol({5: note}, order=[5]))["rows"]
        self.assertEqual(rows[0]["title"], "")

    def test_row_carries_cover_value(self):
        # Cover is user-maintained raw <img> HTML, passed through as-is.
        note = FakeNote(
            content=content_of(4),
            Title="A",
            Cover='<img src="paste-abc.jpg">',
        )
        rows = list_payload(FakeCol({5: note}, order=[5]))["rows"]
        self.assertEqual(rows[0]["cover"], '<img src="paste-abc.jpg">')

    def test_missing_cover_field_is_empty_string(self):
        # A freshly provisioned or adopted note may lack Cover entirely:
        # a missing field yields "" rather than raising (spec: practice-hub
        # → Article list page, empty/absent cover fallback).
        note = FakeNote(content=content_of(4), Title="A")  # no Cover key
        rows = list_payload(FakeCol({5: note}, order=[5]))["rows"]
        self.assertEqual(rows[0]["cover"], "")

    def test_empty_cover_field_is_empty_string(self):
        note = FakeNote(content=content_of(4), Title="A", Cover="")
        rows = list_payload(FakeCol({5: note}, order=[5]))["rows"]
        self.assertEqual(rows[0]["cover"], "")


class ListHtmlTests(unittest.TestCase):
    """Static template checks. Row rendering itself happens at runtime in
    JS (esc()/button loop) and is verified live by the selftest's hub
    check (task 4.1), not here."""

    def test_empty_state_replaces_placeholder_and_payload_has_no_rows(self):
        html = list_html({"rows": []})
        self.assertNotIn("__LSA_DATA__", html)
        self.assertIn("No articles yet", html)  # empty-state message
        raw = html.split("const D = ", 1)[1].split(";", 1)[0]
        self.assertEqual(json.loads(raw), {"rows": []})

    def test_rows_payload_embedded_valid_and_escaped_in_js(self):
        payload = {
            "rows": [
                {
                    "id": 7,
                    "title": "Hello & <World>",
                    "pcts": {"reading": 25, "speaking": 10,
                             "listening": 0, "writing": 100},
                }
            ]
        }
        html = list_html(payload)
        self.assertNotIn("__LSA_DATA__", html)
        raw = html.split("const D = ", 1)[1].split(";", 1)[0]
        embedded = json.loads(raw)
        self.assertEqual(embedded["rows"][0]["id"], 7)
        self.assertEqual(embedded["rows"][0]["pcts"]["reading"], 25)
        # titles are rendered through esc() at runtime, never as raw HTML
        self.assertIn("esc(r.title)", html)

    def test_skill_entries_follow_spec_mode_order(self):
        # Row order is the JS ORDER array: reading, speaking, listening,
        # writing (spec: practice-hub → Article list page).
        html = list_html({"rows": []})
        self.assertIn(
            'const ORDER = ["reading", "speaking", "listening", "writing"]',
            html,
        )
        # each skill entry sends lsa:open:<id>:<mode> through the bridge
        self.assertIn("pycmd('lsa:open:' + b.dataset.open)", html)
        # percent label format "<Skill> <pct>%" (label + ' ' + pct, then
        # the button close appended to the same JS string literal)
        self.assertIn("esc(LABELS[m]) + ' ' + pct + '%</button>'", html)

    def test_cover_is_embedded_unescaped_and_conditional(self):
        # Cover is user-maintained HTML (typically an <img> into the media
        # folder) and must reach the DOM as-is, unlike title (spec:
        # practice-hub → Article list page, cover thumbnail scenario).
        payload = {
            "rows": [
                {
                    "id": 3,
                    "title": "A",
                    "cover": '<img src="paste-abc.jpg">',
                    "pcts": {},
                }
            ]
        }
        html = list_html(payload)
        raw = html.split("const D = ", 1)[1].split(";", 1)[0]
        self.assertEqual(
            json.loads(raw)["rows"][0]["cover"], '<img src="paste-abc.jpg">'
        )
        # rendered raw (no esc() on cover) inside the row's .cover block
        self.assertIn("' + r.cover + '", html)

    def test_cover_thumbnail_css_preserves_aspect_ratio(self):
        # fixed max height with intrinsic width + object-fit crop (spec:
        # practice-hub → Article list page)
        html = list_html({"rows": []})
        self.assertIn(".row .cover img", html)
        self.assertIn("max-height", html)
        self.assertIn("object-fit: cover", html)

    def test_row_layout_is_cover_plus_content_flex(self):
        # each row is a flex container holding the cover block and a
        # .content block of title + skills (empty-cover rows drop the
        # cover block via the ternary, leaving no placeholder)
        html = list_html({"rows": []})
        self.assertIn('const cover = r.cover ? ', html)
        self.assertIn('<div class=\"content\">', html)

    def test_base_tag_rebases_relative_urls_to_media_root(self):
        # Anki serves this page from /_anki/legacyPageData?id=N, so a bare
        # relative src="paste-x.jpg" resolves to /_anki/paste-x.jpg and 404s
        # (Anki's internal web-asset namespace; media lives at the server
        # root). <base href="/"> re-bases it to /paste-x.jpg, which the
        # media server maps to the collection media folder. Removing the
        # tag silently breaks every cover thumbnail — guard it.
        html = list_html({"rows": []})
        self.assertIn('<base href="/">', html)
        # ...and it must sit before any element that resolves URLs
        self.assertLess(html.index('<base href="/">'),
                        html.index('const D = '))


if __name__ == "__main__":
    unittest.main()
