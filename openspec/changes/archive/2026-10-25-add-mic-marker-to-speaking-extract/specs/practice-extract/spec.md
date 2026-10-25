## MODIFIED Requirements

### Requirement: Prefilled note content
For an extracted selection, the system SHALL construct a note targeting deck `English` with per-mode field content (port of the reference app's behavior, plus the Speaking mic decoration):
- **Reading** → note type `@Basic`: `Front` = source context (up to 3 lines above, `<br>`-terminated) with the selection wrapped in `<mark>` + hidden timestamp; `Back` = Youdao dictionary definition, falling back to the translation line at the selected index, else empty.
- **Writing** → note type `@Basic`: selection is made on the **translation** text; `Front` = translation-line context with the selection wrapped in `<mark>` + hidden timestamp; `Back` = the **source line at the same index** (empty when absent). No dictionary lookup.
- **Listening** → note type `@EnListen`: `Front` = source context with the selection **replaced by `???`** + hidden timestamp; `Back` = the **selected text itself**; `Phone` = Youdao phonetics formatted `UK /…/ US /…/` (empty on lookup failure).
- **Speaking** → note type `@EnSpeak`: `Front` = source context with the selection wrapped in `<mark>` **with 🎤 as prefix and suffix of the selected text inside the mark** (i.e. `<mark>🎤selected🎤</mark>`) + hidden timestamp; `Back` = the **selected text itself, undecorated** (no 🎤); `Phone` = Youdao phonetics as above.
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
- **THEN** `Front` wraps the selection in `<mark>` with 🎤 immediately before and after the selected text inside the mark, `Back` equals the selected text without any 🎤, and `Phone` contains the phonetics

#### Scenario: Mic decoration is speaking-only
- **WHEN** the user extracts a selection in Reading, Writing, or Listening mode
- **THEN** `Front` contains no 🎤 anywhere in its field value

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
- **WHEN** the user selects an entire line (selection endpoints at the line's boundaries) and presses `a`
- **THEN** extraction proceeds with start=0 and end=line length
