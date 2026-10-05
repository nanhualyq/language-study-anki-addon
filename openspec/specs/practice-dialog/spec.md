# practice-dialog Specification

## Purpose

Provides the in-Anki practice experience: a Browser-initiated, per-article dialog with four skill modes that render article lines, restore the last learned position, and track learned lines.

## Requirements

### Requirement: Browser context-menu entry
The system SHALL add a context-menu item group to the Browser table menu for selected article notes, offering "Practice: Listening", "Practice: Speaking", "Practice: Reading", and "Practice: Writing". The items SHALL appear only when the selection consists of article notes. Each item's label SHALL append the progress percentage of that skill for the **first selected note** — the note whose dialog opens when the item is chosen — formatted as `<base label> (<percent>%)`, e.g. `Practice: Reading (100%)`.

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
The system SHALL render article content line by line in a web view, with per-mode presentation: Listening shows only a TTS play button per line until the line is expanded to reveal text; Speaking always shows text plus a play button; Reading always shows source lines with a toggle for the matching translation line; Writing shows the translation line with the ability to reveal the corresponding source line.

#### Scenario: Listening mode hides text by default
- **WHEN** the practice dialog opens in Listening mode
- **THEN** each line shows a play button without the source text until the user expands that line

#### Scenario: Reading mode shows translation on toggle
- **WHEN** the user enables the translation toggle in Reading mode
- **THEN** each source line displays its corresponding translation line beneath it, or no translation where none exists

#### Scenario: Writing mode line correspondence
- **WHEN** the user reveals the source line for a translation line in Writing mode
- **THEN** the system shows the source line at the same index, or indicates none exists when the source has fewer lines

#### Scenario: Empty article content
- **WHEN** the dialog opens for an article whose `Content` is empty
- **THEN** the dialog displays an "Article content is empty" message instead of lines

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
