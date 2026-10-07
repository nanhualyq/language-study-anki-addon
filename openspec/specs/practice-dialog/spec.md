# practice-dialog Specification

## Purpose

Provides the in-Anki practice experience: a Browser-initiated, per-article dialog with four skill modes that render article lines, restore the last learned position, and track learned lines.

## Requirements

### Requirement: Browser context-menu entry
The system SHALL add a context-menu item group to the Browser table menu for selected article notes, offering "Practice: Reading", "Practice: Speaking", "Practice: Listening", and "Practice: Writing", in that order. The items SHALL appear only when the selection consists of article notes. Each item's label SHALL append the progress percentage of that skill for the **first selected note** — the note whose dialog opens when the item is chosen — formatted as `<base label> (<percent>%)`, e.g. `Practice: Reading (100%)`.

The percentage SHALL be computed as the note's stored progress line for that skill divided by the total number of lines in the note's `Content`, expressed as an integer percentage rounded to the nearest whole number and clamped to the range 0–100. It SHALL be `0%` when the skill has no progress or `Content` has no lines, and `100%` when the stored progress line reaches or exceeds the line count.

#### Scenario: Right-click an article note
- **WHEN** the user right-clicks a note of the `LSA-Article` note type in the Browser
- **THEN** the context menu contains the four practice items with their percentage suffixes, and choosing one opens the practice dialog for that article in the chosen mode

#### Scenario: Right-click a non-article note
- **WHEN** the user right-clicks a note that is not of the `LSA-Article` note type
- **THEN** no practice items are shown

#### Scenario: Progress shown for the first selected note
- **WHEN** the user right-clicks a multi-note selection consisting entirely of article notes
- **THEN** the percentages in the labels describe the first selected note, matching the dialog that would open

#### Scenario: Percentage calculation
- **WHEN** the first selected article has `Content` of 40 lines, its `ProgReading` is 10, and its `ProgWriting` is 0
- **THEN** the Reading item is labeled `Practice: Reading (25%)` and the Writing item is labeled `Practice: Writing (0%)`

#### Scenario: Stored progress beyond content
- **WHEN** the stored progress line for a skill exceeds the current line count of `Content`
- **THEN** that skill's item shows `100%`

#### Scenario: Empty content
- **WHEN** the first selected article's `Content` is empty
- **THEN** all four items show `0%`

### Requirement: Mode-specific line rendering
The system SHALL render article content line by line in a web view, with per-mode presentation: Listening shows only a TTS play button per line until the user opens that line to reveal text; Speaking always shows source text plus a play button, with the matching translation line available for that line; Reading always shows source lines, with the matching translation line available for a single line and for all lines at once; Writing shows the translation line with the corresponding source line available for that line. In every mode, content that is hidden by default SHALL be shown or hidden only through an explicit per-line toggle control (see the "Per-line reveal control" requirement).

#### Scenario: Listening mode hides text by default
- **WHEN** the practice dialog opens in Listening mode
- **THEN** each line shows a play button without the source text until the user opens that line

#### Scenario: Reading mode shows translation on toggle
- **WHEN** the user enables the translation toggle in Reading mode
- **THEN** each source line displays its corresponding translation line beneath it, or no translation where none exists

#### Scenario: Reading mode shows one line's translation
- **WHEN** the user opens the toggle control of a single line in Reading mode
- **THEN** only that line displays its translation line beneath the source text and every other line is unchanged

#### Scenario: Writing mode line correspondence
- **WHEN** the user reveals the source line for a translation line in Writing mode
- **THEN** the system shows the source line at the same index, or indicates none exists when the source has fewer lines

#### Scenario: Speaking mode translation on demand
- **WHEN** the user opens the toggle control of a single line in Speaking mode
- **THEN** that line displays its translation line beneath the source text and every other line is unchanged

#### Scenario: Empty article content
- **WHEN** the dialog opens for an article whose `Content` is empty
- **THEN** the dialog displays an "Article content is empty" message instead of lines

### Requirement: Per-line reveal control
For every line that has content hidden in the current mode, the system SHALL provide an explicit toggle control that shows or hides that hidden content, and no other interaction with a line SHALL change its visibility. Clicking a line's text, padding, or background — including the click that starts or ends a text selection — SHALL leave the line's visibility unchanged.

#### Scenario: Row click never toggles
- **WHEN** the user clicks a line's text or its empty area in Listening, Speaking, Reading, or Writing mode
- **THEN** no content is shown or hidden, and the click only participates in text selection

#### Scenario: Toggle control reveals and hides that line
- **WHEN** the user activates a line's toggle control in Listening, Writing, Reading, or Speaking mode
- **THEN** that line reveals its hidden content (source text in Listening, source line in Writing, translation line in Reading and Speaking) and activating the same control again hides it

#### Scenario: Toggle control reports its state
- **WHEN** a line is open or closed
- **THEN** its toggle control displays a matching open/closed indicator and exposes the corresponding expanded/collapsed state to assistive technology

#### Scenario: Reading toolbar toggle stays consistent
- **WHEN** the user activates Reading's toolbar translation toggle after having opened or closed individual lines
- **THEN** every line follows the toolbar toggle (all lines open, or all lines closed) and the toolbar label matches the resulting state

#### Scenario: Lines with nothing hidden
- **WHEN** a line has no hidden content in the current mode, such as a line with an empty translation or an empty source line
- **THEN** the line shows a non-interactive placeholder occupying the toggle control's width so that all lines keep the same text indent, and interacting with that placeholder changes nothing

### Requirement: Scroll position restore
The system SHALL restore the dialog's scroll position on open to the line stored in the current mode's progress field, and SHALL clamp a stored position that exceeds the article's current line count to the last line. Stored progress SHALL drive learned-line styling: lines at or below the stored position are marked as learned.

#### Scenario: Restore with history
- **WHEN** the dialog opens in Reading mode and `ProgReading` holds line N within the current line count
- **THEN** the view scrolls to line N and lines 1..N are styled as learned

#### Scenario: No history
- **WHEN** the dialog opens and the current mode's progress field is 0 or unset
- **THEN** the view starts at the first line with no learned lines styled

#### Scenario: Stored position beyond content
- **WHEN** the stored progress line is greater than or equal to the current line count (for example, after the article was shortened)
- **THEN** the view scrolls to the last line without error

### Requirement: Selection capture
The system SHALL capture text selections within the practice view, recording the selected text, its line number (1-based), and the full line text, and expose the selection to the extract command. Deselecting or selecting across nothing SHALL clear the current selection.

#### Scenario: Selection within one line
- **WHEN** the user selects a substring of line 7
- **THEN** the current selection records the selected substring, line number 7, and line 7's full text

#### Scenario: No selection
- **WHEN** the user triggers extraction with no active selection
- **THEN** no extraction occurs and no dialog is opened
