# practice-extract Specification

## Purpose

Turns selected text from a practice session into a vocabulary note prefilled in Anki's Add dialog, with dictionary-backed definitions and article context, replacing the external AnkiConnect hop with direct in-process note construction.

## Requirements

### Requirement: Keyboard shortcut triggers extraction
The system SHALL provide a `Ctrl+E` shortcut in the practice dialog that sends the current selection to Anki's Add dialog. The shortcut SHALL have no effect when no selection exists. When a required note type or deck is missing, the shortcut SHALL first obtain the user's confirmation to create it; declining cancels the extraction.

#### Scenario: Shortcut with active selection
- **WHEN** the user has a selection in the practice view and presses `Ctrl+E`
- **THEN** Anki's Add dialog opens with a prefilled note as specified below

#### Scenario: Shortcut without selection
- **WHEN** the user presses `Ctrl+E` with no active selection
- **THEN** nothing happens: no dialog opens and no note is constructed

#### Scenario: Missing note types declined during extraction
- **WHEN** the user presses `Ctrl+E` while required note types or decks are missing and declines the creation confirmation
- **THEN** extraction is cancelled: no Add dialog opens and no note is constructed

### Requirement: Prefilled note content
For an extracted selection, the system SHALL construct a note targeting deck `English` with per-mode field content (port of the reference app's behavior):
- **Reading** → note type `@Basic`: `Front` = source context (up to 3 lines above, `<br>`-terminated) with the selection wrapped in `<mark>` + hidden timestamp; `Back` = Youdao dictionary definition, falling back to the translation line at the selected index, else empty.
- **Writing** → note type `@Basic`: selection is made on the **translation** text; `Front` = translation-line context with the selection wrapped in `<mark>` + hidden timestamp; `Back` = the **source line at the same index** (empty when absent). No dictionary lookup.
- **Listening** → note type `@EnListen`: `Front` = source context with the selection **replaced by `???`** + hidden timestamp; `Back` = the **selected text itself**; `Phone` = Youdao phonetics formatted `UK /…/ US /…/` (empty on lookup failure).
- **Speaking** → note type `@EnSpeak`: `Front` = source context with the selection wrapped in `<mark>` + hidden timestamp; `Back` = the **selected text itself**; `Phone` = Youdao phonetics as above.
- All types also carry `Title` (article title) and `Url` (article URL or empty). Audio types additionally carry `Phone`.
All inter-line separators in field values SHALL be `<br>` tags, never raw newlines.

#### Scenario: Reading extraction with dictionary result
- **WHEN** the user extracts a selection in Reading mode whose Youdao lookup returns entries
- **THEN** `Back` contains the dictionary definition and `Front` contains the 3-line context with the selection wrapped in `<mark>`

#### Scenario: Reading dictionary returns nothing
- **WHEN** the Youdao lookup returns no entries for the selected text
- **THEN** `Back` contains the translation line at the selected line's index, if it exists; otherwise `Back` is empty

#### Scenario: Listening masks the selection
- **WHEN** the user extracts a selection in Listening mode
- **THEN** `Front` contains the context lines with the selection replaced by `???`, `Back` equals the selected text, and `Phone` contains the phonetics (or is empty when the lookup fails)

#### Scenario: Speaking shows the selection
- **WHEN** the user extracts a selection in Speaking mode
- **THEN** `Front` wraps the selection in `<mark>`, `Back` equals the selected text, and `Phone` contains the phonetics

#### Scenario: Writing extracts the translation
- **WHEN** the user selects text on a translation line in Writing mode and extracts
- **THEN** `Front` is built from the **translation** lines with the selection wrapped in `<mark>`, and `Back` contains the source line at the same index
- **AND** no dictionary lookup is performed

#### Scenario: Selection on the first line
- **WHEN** the user extracts a selection on line 1
- **THEN** `Front` contains no context lines above it, only the marked/masked selected line and the hidden timestamp

#### Scenario: Extraction near the top of the article
- **WHEN** the selected line's index is less than 3 lines from the start
- **THEN** only the available context lines (down to line 1) are included above it

#### Scenario: Whole-line selection extracts
- **WHEN** the user selects an entire line (selection endpoints at the line's boundaries) and presses `Ctrl+E`
- **THEN** extraction proceeds with start=0 and end=line length

### Requirement: Dictionary lookup failure tolerance
The system SHALL treat Youdao lookup network failures and timeouts as empty results and SHALL NOT surface errors that interrupt extraction.

#### Scenario: Network unavailable
- **WHEN** the Youdao request fails or times out during extraction
- **THEN** extraction continues with the translation-line fallback (or empty `Back`), and the Add dialog still opens

### Requirement: Prefilled Add dialog handoff
The system SHALL open Anki's native Add dialog with the constructed note prefilled, without creating the note until the user confirms. Extraction SHALL NOT require AnkiConnect or any external process.

#### Scenario: User confirms
- **WHEN** the Add dialog opens with the prefilled note and the user confirms
- **THEN** the note is added to deck `English` with the chosen note type

#### Scenario: User cancels
- **WHEN** the Add dialog opens and the user cancels
- **THEN** no note is created

### Requirement: Extraction updates skill progress
After the Add dialog is opened for an extraction from line N, the system SHALL set the current mode's progress field to at least N.

#### Scenario: Progress advances on extract
- **WHEN** the user extracts from line N in Reading mode and `ProgReading` holds a value below N
- **THEN** `ProgReading` is set to N after the extraction flow completes
