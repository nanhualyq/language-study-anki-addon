"""Unit tests for browser context-menu label percentages.

Change: add-progress-percents-to-browser-menu (spec: practice-dialog →
Browser context-menu entry).

Zero-dependency style like the rest of tests/: `aqt` is not installed, so the
package is imported FIRST (its init() skips Anki hook registration when aqt is
absent), then a minimal `aqt.qt` stub is installed so `practice_dialog`
imports cleanly.
"""

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
    aqt.qt = qt
    sys.modules["aqt"] = aqt
    sys.modules["aqt.qt"] = qt


_stub_aqt_qt()

from language_study_anki.browser_menu import (  # noqa: E402
    _progress_percent,
    build_menu_labels,
)
from language_study_anki.provisioning import ARTICLE_NOTE_TYPE  # noqa: E402

MODES = ("listening", "speaking", "reading", "writing")
BASE_LABELS = {
    "listening": "Practice: Listening",
    "speaking": "Practice: Speaking",
    "reading": "Practice: Reading",
    "writing": "Practice: Writing",
}


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
    def __init__(self, notes):
        self.notes = notes

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


class BuildMenuLabelsTests(unittest.TestCase):
    def test_labels_carry_percent_suffixes(self):
        note = FakeNote(content=content_of(40), ProgReading="10")
        col = FakeCol({1: note})
        labels = build_menu_labels([1], col)
        self.assertEqual(
            labels,
            [
                ("listening", "Practice: Listening (0%)"),
                ("speaking", "Practice: Speaking (0%)"),
                ("reading", "Practice: Reading (25%)"),
                ("writing", "Practice: Writing (0%)"),
            ],
        )
        self.assertEqual([m for m, _ in labels], list(MODES))

    def test_percentages_come_from_first_selected_note(self):
        first = FakeNote(content=content_of(40), ProgReading="40")   # 100%
        second = FakeNote(content=content_of(40), ProgReading="10")  # 25%
        col = FakeCol({1: first, 2: second})
        labels = dict(build_menu_labels([1, 2], col))
        self.assertEqual(labels["reading"], "Practice: Reading (100%)")
        # Selection order changes which note is "first": now the 25% one.
        labels_rev = dict(build_menu_labels([2, 1], col))
        self.assertEqual(labels_rev["reading"], "Practice: Reading (25%)")

    def test_empty_content_shows_zero_everywhere(self):
        note = FakeNote(content="", ProgReading="10")
        labels = build_menu_labels([1], FakeCol({1: note}))
        self.assertTrue(all(label.endswith("(0%)") for _, label in labels))

    def test_mixed_selection_returns_none(self):
        art = FakeNote(content=content_of(40))
        basic = FakeNote(content="x", note_type_name="@Basic")
        self.assertIsNone(build_menu_labels([1, 2], FakeCol({1: art, 2: basic})))

    def test_non_article_selection_returns_none(self):
        basic = FakeNote(content="x", note_type_name="@Basic")
        self.assertIsNone(build_menu_labels([1], FakeCol({1: basic})))

    def test_empty_selection_returns_none(self):
        self.assertIsNone(build_menu_labels([], FakeCol({})))

    def test_missing_note_returns_none(self):
        self.assertIsNone(build_menu_labels([99], FakeCol({})))


if __name__ == "__main__":
    unittest.main()
