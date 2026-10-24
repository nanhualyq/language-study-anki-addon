## ADDED Requirements

### Requirement: Toolbar progress counter and selection hint
The practice dialog SHALL show a toolbar pinned to the top of the view that remains visible while the article scrolls, displaying the current mode, a learned-progress counter for the mode, and a text-selection hint. The progress counter SHALL be formatted as `<learned>/<total>`, where `<total>` is the number of lines in the article's content and `<learned>` is the mode's stored progress clamped to that count, so the counter never exceeds the total. The hint SHALL state the selection-to-extract action and render the shortcut key in a visually distinct keycap treatment, distinguishable from the surrounding plain text, and SHALL sit at the toolbar's right end so that no hint element overlaps the article body. When an extraction advances the mode's progress, the counter SHALL update immediately without reopening the dialog. No toolbar control SHALL reveal hidden per-line content in bulk.

#### Scenario: Counter shows learned over total
- **WHEN** the dialog opens in a mode whose stored progress is line 12 and the article's content has 50 lines
- **THEN** the toolbar progress counter displays `12/50`

#### Scenario: Stored progress beyond content is clamped
- **WHEN** the dialog opens in a mode whose stored progress is 60 and the article's content has 50 lines
- **THEN** the toolbar progress counter displays `50/50`

#### Scenario: Counter updates immediately after extraction
- **WHEN** an extraction advances the current mode's stored progress from line 12 to line 13
- **THEN** the toolbar progress counter immediately displays `13/<total>` without the dialog being reopened

#### Scenario: Empty article content
- **WHEN** the dialog opens for an article whose content has no lines
- **THEN** the toolbar progress counter displays `0/0`

#### Scenario: Hint sits in the toolbar, not over the article
- **WHEN** the practice dialog renders
- **THEN** the selection hint is visible within the toolbar at its right end, and no hint element covers any part of the article body

#### Scenario: Shortcut key is visually distinct
- **WHEN** the user looks at the selection hint in the toolbar
- **THEN** the shortcut key (`a`) is rendered in a keycap treatment — visually separated from the adjacent hint words, for example by a border and background — rather than as plain inline text

#### Scenario: No bulk reveal control in the toolbar
- **WHEN** the dialog is open in any mode
- **THEN** the toolbar provides no control that shows or hides hidden content for all lines at once

## MODIFIED Requirements

### Requirement: Mode-specific line rendering
The system SHALL render article content line by line in a web view, with per-mode presentation: Listening shows only a TTS play button per line until the user opens that line to reveal text; Speaking always shows source text plus a play button, with the matching translation line available for that line; Reading always shows source lines, with the matching translation line available for that line; Writing shows the translation line with the corresponding source line available for that line. In every mode, content that is hidden by default SHALL be shown or hidden only through an explicit per-line toggle control (see the "Per-line reveal control" requirement).

#### Scenario: Listening mode hides text by default
- **WHEN** the practice dialog opens in Listening mode
- **THEN** each line shows a play button without the source text until the user opens that line

#### Scenario: Reading mode shows translation on toggle
- **WHEN** the user activates a line's toggle control in Reading mode
- **THEN** that line displays its translation beneath the source text, all other lines are unchanged, and the toolbar provides no control that reveals all translations at once

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

#### Scenario: Reading toolbar toggle stays consistent
- **WHEN** the user opens or closes individual lines in Reading mode
- **THEN** no toolbar control overrides those per-line states, and each line's toggle control continues to display an indicator matching that line's actual visibility

#### Scenario: Toggle control reports its state
- **WHEN** a line is open or closed
- **THEN** its toggle control displays a matching open/closed indicator and exposes the corresponding expanded/collapsed state to assistive technology

#### Scenario: Lines with nothing hidden
- **WHEN** a line has no hidden content in the current mode, such as a line with an empty translation or an empty source line
- **THEN** the line shows a non-interactive placeholder occupying the toggle control's width so that all lines keep the same text indent, and interacting with that placeholder changes nothing
