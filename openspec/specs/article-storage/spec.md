# article-storage Specification

## Purpose

Stores English articles and per-skill learning progress as native Anki notes, so the article library lives inside the collection, syncs with it, and never pollutes the review queue.

## Requirements

### Requirement: Article note type
The system SHALL represent an article as an Anki note of an addon-provisioned `LSA-Article` note type with fields `Title`, `Content`, `Translation`, `Url`, `ProgListening`, `ProgSpeaking`, `ProgReading`, and `ProgWriting`. `Title` SHALL be the sort field. `Translation` and `Url` MAY be empty.

#### Scenario: Store an article with all fields
- **WHEN** the user creates an article note with a title, English content, a Chinese translation, and a URL
- **THEN** the system stores all values in the corresponding fields of a single note

#### Scenario: Store an article without translation or URL
- **WHEN** the user creates an article note with a title and English content only
- **THEN** the `Translation` and `Url` fields are stored as empty strings

### Requirement: Auto-provisioning of note types and deck
The system SHALL provision its note types and decks in two stages, each gated by user confirmation. At profile open, when the `LSA-Article` note type is missing, the system SHALL show one confirmation dialog listing exactly the missing items and create them only when the user accepts. At extraction time, when the extract target note types (`LSA-ReadWrite`, `LSA-Listen`, `LSA-Speak`) or target deck (`English`) are missing, the system SHALL show the same kind of confirmation before creating them, and declining cancels the extraction. Existing note types and decks SHALL be adopted by exact name when present, and provisioning SHALL be idempotent. The system SHALL NOT create or require a dedicated article deck.

#### Scenario: First use on a clean collection
- **WHEN** the user opens a profile for the first time in a collection lacking the `LSA-Article` note type
- **THEN** the system shows one confirmation dialog listing exactly the missing items, and creates them once the user accepts, without further setup

#### Scenario: Nothing missing at profile open
- **WHEN** a profile opens and the `LSA-Article` note type already exists
- **THEN** no dialog is shown and nothing is created

#### Scenario: Startup confirmation declined
- **WHEN** the user declines the startup confirmation dialog
- **THEN** nothing is created at that moment, and the same confirmation is offered again at the next profile open

#### Scenario: Extract targets created at extraction time
- **WHEN** the user extracts a selection and any extract target note type or the `English` deck is missing
- **THEN** the system shows a confirmation listing exactly the missing items before creating anything

#### Scenario: Extract-time confirmation declined
- **WHEN** the user declines the extraction-time confirmation
- **THEN** extraction is cancelled: no Add dialog opens and no note is created

#### Scenario: Headless self-test runs unattended
- **WHEN** the addon runs under its self-test harness
- **THEN** provisioning proceeds automatically without displaying any confirmation dialog

#### Scenario: Existing note types are adopted
- **WHEN** the collection already contains note types named `LSA-ReadWrite`, `LSA-Listen`, or `LSA-Speak`, or decks named `English`
- **THEN** the system uses those existing note types and decks instead of creating duplicates

### Requirement: Legacy extract note types are never adopted
The system SHALL recognize and provision the extract target note types exclusively under the names `LSA-ReadWrite`, `LSA-Listen`, and `LSA-Speak`. Pre-existing note types carrying the legacy names (`@Basic`, `@EnListen`, `@EnSpeak`) SHALL be left untouched: the system SHALL NOT rename them, adopt them, or migrate their notes, and any collection containing only legacy types SHALL be treated as missing the extract targets.

#### Scenario: Collection has only legacy extract types
- **WHEN** the user extracts from a collection that contains note types named `@Basic`, `@EnListen`, or `@EnSpeak` but not the corresponding `LSA-*` types
- **THEN** the extraction-time confirmation lists the missing `LSA-*` note types, and accepting creates them without renaming or modifying the legacy note types

#### Scenario: Legacy notes stay on legacy types
- **WHEN** the user extracts after the `LSA-*` types have been provisioned in a collection that previously held notes on the legacy types
- **THEN** the new note is created on the `LSA-*` note type, and the legacy notes remain attached to their legacy note types unchanged

### Requirement: Articles never enter the review queue
The system SHALL ensure each article note's generated card is suspended at creation time, so articles never appear during study. Article residence in any particular deck SHALL NOT be required or enforced.

#### Scenario: Article note created
- **WHEN** the system creates an article note
- **THEN** the card generated from the note is suspended

#### Scenario: Article note edited
- **WHEN** an existing article note is edited such that its card would be regenerated or unsuspended
- **THEN** the article's card remains suspended and excluded from review queues after the edit

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

### Requirement: Per-skill progress fields
The system SHALL store each skill's progress as a separate integer field (`ProgListening`, `ProgSpeaking`, `ProgReading`, `ProgWriting`) holding the 1-based last extracted line number for that skill, with `0` meaning no progress. Progress SHALL be written only when a practice session extracts content — never on scrolling and never when the practice dialog closes.

#### Scenario: Extract updates progress
- **WHEN** the user extracts a selection from line N of an article in a practice mode
- **THEN** that mode's progress field is set to at least N, and no other skill's progress field is modified

#### Scenario: Scrolling and closing do not write progress
- **WHEN** the user scrolls within the practice dialog and closes it without extracting
- **THEN** no progress field is modified

#### Scenario: Progress never decreases
- **WHEN** the user extracts from line N while the current mode's progress field already holds a value greater than N
- **THEN** the stored progress line is not reduced below its previous value

#### Scenario: Field-level conflict isolation
- **WHEN** two skills are practiced on two devices that later sync
- **THEN** each skill's progress lives in its own field, so a sync conflict affects at most one skill's progress field
