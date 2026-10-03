## Purpose

Stores English articles and per-skill learning progress as native Anki notes, so the article library lives inside the collection, syncs with it, and never pollutes the review queue.

## ADDED Requirements

### Requirement: Article note type
The system SHALL represent an article as an Anki note of an addon-provisioned `Article` note type with fields `Title`, `Content`, `Translation`, `Url`, `ProgListening`, `ProgSpeaking`, `ProgReading`, and `ProgWriting`. `Title` SHALL be the sort field. `Translation` and `Url` MAY be empty.

#### Scenario: Store an article with all fields
- **WHEN** the user creates an article note with a title, English content, a Chinese translation, and a URL
- **THEN** the system stores all values in the corresponding fields of a single note

#### Scenario: Store an article without translation or URL
- **WHEN** the user creates an article note with a title and English content only
- **THEN** the `Translation` and `Url` fields are stored as empty strings

### Requirement: Auto-provisioning of note types and deck
The system SHALL create the `Article` note type, the dedicated article deck, and the extract target note types (`@Basic`, `@EnListen`, `@EnSpeak`) and target deck (`English`) if they do not already exist, and SHALL adopt existing ones by exact name when present. Provisioning SHALL be idempotent.

#### Scenario: First use on a clean collection
- **WHEN** the user opens the practice entry for the first time in a collection lacking the required note types and decks
- **THEN** the system creates the missing note types and decks before proceeding, without user setup

#### Scenario: Existing note types are adopted
- **WHEN** the collection already contains note types named `@Basic`, `@EnListen`, or `@EnSpeak`, or decks named `English`
- **THEN** the system uses those existing note types and decks instead of creating duplicates

### Requirement: Articles never enter the review queue
The system SHALL ensure each article note's generated card is suspended at creation time and resides in the dedicated article deck, so articles never appear during study.

#### Scenario: Article note created
- **WHEN** the system creates an article note
- **THEN** the card generated from the note is suspended and belongs to the dedicated article deck

#### Scenario: Article note edited
- **WHEN** an existing article note is edited such that its card would be regenerated or unsuspended
- **THEN** the article's card remains suspended and excluded from review queues after the edit

### Requirement: Line-based content storage
The system SHALL store `Content` and `Translation` as line sequences with `<br>` as the canonical line separator, and SHALL parse existing content tolerantly — splitting on `<br>` first and falling back to `\n` — so content written by the system and content edited through Anki's rich editor both yield correct line sequences.

#### Scenario: Content created by the system
- **WHEN** the system writes multi-line article content to a note field
- **THEN** the stored value separates lines with `<br>`, and parsing returns the original line sequence

#### Scenario: Content edited in Anki's rich editor
- **WHEN** a user edits an article note's content in Anki's editor and the editor rewrites line breaks in its own HTML form
- **THEN** the parser still reconstructs the intended line sequence without dropping or merging lines

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
