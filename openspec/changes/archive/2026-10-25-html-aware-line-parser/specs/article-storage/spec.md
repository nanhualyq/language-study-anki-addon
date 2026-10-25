## MODIFIED Requirements

### Requirement: Line-based content storage
The system SHALL store `Content` and `Translation` as line sequences with `<br>` as the canonical line separator, and SHALL parse stored field HTML structurally rather than by text substitution, so that the intended line sequence is reconstructed for every markup shape the system or Anki's editors produce. Structural parsing SHALL observe these rules:

- a block-level element that contains other block elements (a wrapper such as the editor's outer `<div>` or a pasted container) contributes no line of its own;
- a block-level element that contains no block descendants contributes exactly one line — its content, with an empty element contributing an empty line when it sits between other content;
- `<br>` is a hard line break, splitting one block into multiple lines;
- element attributes and inline markup do not affect line boundaries; text is yielded unescaped, so entity-escaped markup characters are data, never separators;
- the content of `script`, `style`, and comments, whitespace-only text between elements, and CRLF line endings are normalized away rather than becoming lines or line fragments.

The parser SHALL drop leading and trailing empty lines so document-edge markup artifacts never appear as content, SHALL preserve empty lines between non-empty lines, and SHALL return zero lines for an empty or whitespace-only value. A field that begins or ends with a blank line is therefore not representable; interior blank lines round-trip.

#### Scenario: Content created by the system
- **WHEN** the system writes multi-line article content to a note field
- **THEN** the stored value separates lines with `<br>`, and parsing returns the original line sequence

#### Scenario: Content edited in Anki's rich editor
- **WHEN** a user edits an article note's content in Anki's editor and the editor rewrites line breaks in its own HTML form
- **THEN** the parser still reconstructs the intended line sequence without dropping or merging lines

#### Scenario: Editor wrapper markup yields no phantom lines
- **WHEN** `Content` is stored as an outer `<div>` wrapping one `<div>` per line of a 56-line article, as written by Anki's rich editor after a user edit
- **THEN** parsing returns exactly 56 lines whose last line is the article's final text line, with no empty trailing lines

#### Scenario: Empty paragraph between content lines is preserved
- **WHEN** the stored value contains an empty block element (or an element containing only `<br>`) between two text lines
- **THEN** parsing returns exactly one empty line at that position, between the two text lines

#### Scenario: Document-edge artifacts are dropped
- **WHEN** the stored value ends with an empty block, a trailing `<br>`, or duplicated trailing separators (or begins with the equivalent artifacts)
- **THEN** parsing returns no leading or trailing empty lines — the first and last returned lines are the article's first and last real text lines

#### Scenario: Web-pasted markup
- **WHEN** content pasted from a web page stores its lines as `<div>`/`<p>` blocks with class attributes, includes a `<ul><li>` list, and contains a `<style>` block
- **THEN** each text block and list item yields one line, the `style` block's text yields no lines, and element attributes do not alter the result

#### Scenario: Unclosed paragraph
- **WHEN** pasted or hand-edited markup contains consecutive paragraph opens without closes, such as `<p>first<p>second`
- **THEN** parsing returns two lines, `first` and `second`

#### Scenario: Entities and line endings are data, not syntax
- **WHEN** a field contains `x &lt;br&gt; y` and lines separated by `\r\n`
- **THEN** parsing returns `x <br> y` as a single line and yields each CRLF-separated line without a trailing `\r` character

#### Scenario: Empty content
- **WHEN** `Content` is an empty string
- **THEN** parsing returns zero lines and the practice layer treats the article as empty
