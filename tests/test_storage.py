import pathlib
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
        self.assertEqual(
            field_to_lines("<p>line one</p><p>line two</p>"),
            ["line one", "line two"],
        )

    def test_editor_div_wrappers(self):
        self.assertEqual(
            field_to_lines("<div>alpha</div><div>beta</div>"),
            ["alpha", "beta"],
        )

    def test_entities_unescaped(self):
        self.assertEqual(field_to_lines("a &amp; b<br>c &lt; d"), ["a & b", "c < d"])

    def test_escaped_br_text_stays_single_line(self):
        # Literal text "&#60;br&#62;" must not be treated as a separator.
        self.assertEqual(field_to_lines("x &lt;br&gt; y"), ["x <br> y"])

    def test_nbsp_normalized(self):
        self.assertEqual(field_to_lines("a&nbsp;b"), ["a b"])

    def test_crlf_lines_carry_no_carriage_return(self):
        self.assertEqual(field_to_lines("a\r\nb\r\nc"), ["a", "b", "c"])


def wrapped_article_content(n: int) -> str:
    """Anki rich-editor shape after a user edit: an outer <div> wrapping
    one <div> per line (captured live: 56-line article, ProgReading 54)."""
    body = "".join(f"<div>line {i}</div>" for i in range(1, n + 1))
    return f"<div>{body}</div>"


class StructuralMarkupTests(unittest.TestCase):
    """Spec delta: article-storage → Line-based content storage.

    The structural rule — leaf block = one line, container block = no line,
    <br> = hard break, document-edge empties dropped — replaces the old
    regex pipeline that turned every </div> (including wrapper closes) into
    a phantom line.
    """

    def test_editor_wrapper_yields_no_phantom_lines(self):
        lines = field_to_lines(wrapped_article_content(56))
        self.assertEqual(len(lines), 56)
        self.assertEqual(lines[0], "line 1")
        self.assertEqual(lines[-1], "line 56")
        self.assertNotIn("", lines)

    def test_wrapper_plus_sibling_block_has_no_middle_phantom(self):
        self.assertEqual(
            field_to_lines("<div><div>A</div></div><div>B</div>"),
            ["A", "B"],
        )

    def test_empty_paragraph_between_lines_is_preserved(self):
        self.assertEqual(
            field_to_lines("<div>A</div><div></div><div>B</div>"),
            ["A", "", "B"],
        )

    def test_br_only_paragraph_is_one_blank_line(self):
        self.assertEqual(
            field_to_lines("<div>A</div><div><br></div><div>B</div>"),
            ["A", "", "B"],
        )

    def test_trailing_br_is_dropped(self):
        self.assertEqual(field_to_lines("A<br>B<br>"), ["A", "B"])

    def test_trailing_empty_block_is_dropped(self):
        self.assertEqual(field_to_lines("<div>A</div><div></div>"), ["A"])

    def test_duplicated_trailing_separators_are_dropped(self):
        self.assertEqual(field_to_lines("A<br><br>"), ["A"])

    def test_leading_artifacts_are_dropped(self):
        self.assertEqual(field_to_lines("<div></div><div>A</div>"), ["A"])
        self.assertEqual(field_to_lines("<br>A"), ["A"])

    def test_leaf_ending_with_br_is_not_doubled(self):
        self.assertEqual(field_to_lines("<div>A<br></div>"), ["A"])

    def test_web_pasted_markup(self):
        pasted = (
            '<p class="intro">first</p>'
            '<style>p { color: red; }</style>'
            '<p data-x="1">second</p>'
            '<ul><li>item one</li><li>item two</li></ul>'
        )
        self.assertEqual(
            field_to_lines(pasted),
            ["first", "second", "item one", "item two"],
        )

    def test_unclosed_paragraphs(self):
        self.assertEqual(field_to_lines("<p>first<p>second"), ["first", "second"])

    def test_malformed_markup_never_raises(self):
        # Stray/mismatched closes and crossed nesting must be tolerated.
        self.assertEqual(field_to_lines("<div><p>mismatch</div>"), ["mismatch"])
        self.assertEqual(field_to_lines("stray</div>loose text"), ["strayloose text"])
        self.assertEqual(field_to_lines("<p>a<div>b</p>"), ["a", "b"])
        self.assertEqual(
            field_to_lines("<ul><li>a<ul><li>b</li></ul></li>"),
            ["a", "b"],
        )

    def test_void_and_media_elements_do_not_affect_lines(self):
        self.assertEqual(
            field_to_lines("<div><img src='x.png'></div><div>next</div>"),
            ["next"],  # image-only line is empty; at the edge it is trimmed
        )
        self.assertEqual(field_to_lines("<hr>text"), ["text"])


class RealNoteRegressionTests(unittest.TestCase):
    """Fixture reproducing the shape captured from a real Anki rich-editor
    write: an outer <div> wrapping one <div> per line for a 56-line article
    (the old regex parser returned 58 lines with the last two empty).
    The text is synthetic so the fixture is safe to publish."""

    FIXTURE = (
        pathlib.Path(__file__).parent
        / "fixtures"
        / "article_content_editor_wrapper.html"
    )

    def test_captured_article_parses_to_exactly_56_lines(self):
        content = self.FIXTURE.read_text(encoding="utf-8")
        lines = field_to_lines(content)
        self.assertEqual(len(lines), 56)
        self.assertTrue(lines[0].startswith("Fixture line 01:"))
        self.assertTrue(lines[-1].startswith("Fixture line 56:"))
        self.assertNotIn("", lines)

    def test_inline_markup_does_not_break_lines(self):
        self.assertEqual(
            field_to_lines("<div>one <b>bold</b></div><div><span>two</span></div>"),
            ["one bold", "two"],
        )


if __name__ == "__main__":
    unittest.main()
