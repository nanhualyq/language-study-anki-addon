import re
import unittest

from language_study_anki.field_builder import (
    build_front,
    format_back,
    resolve_back,
)
from language_study_anki.youdao import DictEntry


def lines(n):
    return [f"line {i + 1}" for i in range(n)]


class BuildFrontTests(unittest.TestCase):
    def test_first_line_has_no_context(self):
        front = build_front(lines(10), 1, 0, 4, timestamp_ms=123)
        self.assertNotIn("line 0", front)
        self.assertIn("<mark>line</mark> 1", front)
        self.assertTrue(front.endswith('<span style="display:none">123</span>'))

    def test_mid_article_gets_three_context_lines(self):
        front = build_front(lines(10), 7, 0, 4, timestamp_ms=1)
        # Context: lines 4,5,6 with <br> terminators, then the marked line 7.
        self.assertIn("line 4<br>line 5<br>line 6<br>", front)
        self.assertIn("<mark>line</mark> 7", front)
        self.assertNotIn("line 3<br>", front)
        self.assertNotIn("line 8", front)

    def test_near_top_clamps_to_first_line(self):
        front = build_front(lines(10), 2, 0, 4, timestamp_ms=1)
        self.assertIn("line 1<br>", front)
        self.assertNotIn("line 0", front)

    def test_no_raw_newlines_in_field(self):
        front = build_front(lines(10), 5, 0, 4, timestamp_ms=1)
        self.assertNotIn("\n", front)

    def test_context_lines_escaped(self):
        content = ["a < b", "plain", "target"]
        front = build_front(content, 3, 0, 6, timestamp_ms=1)
        self.assertIn("a &lt; b<br>", front)
        self.assertIn("<mark>target</mark>", front)

    def test_highlight_replacement(self):
        front = build_front(lines(3), 1, 0, 6, highlight_replacement="???", timestamp_ms=1)
        self.assertIn("<mark>???</mark>", front)
        self.assertNotIn("<mark>line 1</mark>", front)

    def test_selection_offsets_preserve_surroundings(self):
        front = build_front(["abc def ghi"], 1, 4, 7, timestamp_ms=1)
        self.assertIn("abc <mark>def</mark> ghi", front)

    def test_default_timestamp_is_hidden_numeric_span(self):
        span = re.compile(r'<span style="display:none">\d+</span>')
        front = build_front(lines(3), 1, 0, 4)
        self.assertRegex(front, span)
        # Distinct timestamps yield distinct content (uniqueness basis).
        a = build_front(lines(3), 1, 0, 4, timestamp_ms=1000)
        b = build_front(lines(3), 1, 0, 4, timestamp_ms=2000)
        self.assertNotEqual(a, b)

    def test_out_of_range_line_raises(self):
        with self.assertRaises(IndexError):
            build_front(lines(3), 4, 0, 1, timestamp_ms=1)
        with self.assertRaises(IndexError):
            build_front([], 1, 0, 1, timestamp_ms=1)

    def test_out_of_range_offsets_raise(self):
        with self.assertRaises(IndexError):
            build_front(["abc"], 1, 2, 99, timestamp_ms=1)


class BackResolutionTests(unittest.TestCase):
    def test_dictionary_entries_win(self):
        entries = [DictEntry(pos="adj.", tran="短暂的")]
        back = resolve_back(entries, ["翻译行"], 1)
        self.assertEqual(back, "adj. 短暂的")

    def test_multiple_entries_joined_by_br(self):
        entries = [DictEntry(pos="adj.", tran="短暂的"), DictEntry(pos="n.", tran="片刻")]
        self.assertEqual(format_back(entries), "adj. 短暂的<br>n. 片刻")

    def test_no_entries_falls_back_to_translation_line(self):
        back = resolve_back([], ["第一行翻译", "第二行翻译"], 2)
        self.assertEqual(back, "第二行翻译")

    def test_no_entries_and_no_matching_line_is_empty(self):
        self.assertEqual(resolve_back([], ["only one line"], 5), "")

    def test_empty_translation_line_yields_empty_string(self):
        self.assertEqual(resolve_back([], [], 1), "")

    def test_translation_line_escaped(self):
        back = resolve_back([], ["a < b"], 1)
        self.assertEqual(back, "a &lt; b")


if __name__ == "__main__":
    unittest.main()
