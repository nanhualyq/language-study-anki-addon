## MODIFIED Requirements

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

## ADDED Requirements

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
