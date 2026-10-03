import unittest

from language_study_anki.storage import field_to_lines, lines_to_field


class RoundTripTests(unittest.TestCase):
    def test_writer_uses_br_separator(self):
        self.assertEqual(lines_to_field(["a", "b"]), "a<br>b")

    def test_writer_escapes_html(self):
        self.assertEqual(
            lines_to_field(["a < b", "x & y"]),
            "a &lt; b<br>x &amp; y",
        )

    def test_round_trip(self):
        lines = ["first line", "second <tag> & more", "third"]
        self.assertEqual(field_to_lines(lines_to_field(lines)), lines)

    def test_round_trip_with_empty_line(self):
        lines = ["a", "", "b"]
        self.assertEqual(field_to_lines(lines_to_field(lines)), lines)


class TolerantParserTests(unittest.TestCase):
    def test_empty_value_yields_no_lines(self):
        self.assertEqual(field_to_lines(""), [])
        self.assertEqual(field_to_lines(None), [])
        self.assertEqual(field_to_lines("   "), [])

    def test_br_split(self):
        self.assertEqual(field_to_lines("a<br>b"), ["a", "b"])
        self.assertEqual(field_to_lines("a<br/>b<br />c"), ["a", "b", "c"])

    def test_raw_newline_fallback(self):
        self.assertEqual(field_to_lines("a\nb"), ["a", "b"])

    def test_mixed_separators(self):
        self.assertEqual(field_to_lines("a<br>b\nc"), ["a", "b", "c"])

    def test_editor_paragraph_wrappers(self):
        # Anki rich-editor style block markup: one line per paragraph.
        self.assertEqual(field_to_lines("<p>line one</p><p>line two</p>")[:2], ["line one", "line two"])

    def test_editor_div_wrappers(self):
        self.assertEqual(field_to_lines("<div>alpha</div><div>beta</div>")[:2], ["alpha", "beta"])

    def test_entities_unescaped(self):
        self.assertEqual(field_to_lines("a &amp; b<br>c &lt; d"), ["a & b", "c < d"])

    def test_escaped_br_text_stays_single_line(self):
        # Literal text "&#60;br&#62;" must not be treated as a separator.
        self.assertEqual(field_to_lines("x &lt;br&gt; y"), ["x <br> y"])

    def test_nbsp_normalized(self):
        self.assertEqual(field_to_lines("a&nbsp;b"), ["a b"])


if __name__ == "__main__":
    unittest.main()
