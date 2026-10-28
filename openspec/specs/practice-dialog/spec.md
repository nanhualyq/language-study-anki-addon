# practice-dialog Specification

## Purpose

Provides the in-Anki practice experience: the per-article practice view — rendered inside the practice-hub window — with four skill modes that render article lines, restore the last learned position, and track learned lines.

## Requirements

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

### Requirement: Toolbar progress counter and selection hint
The practice view SHALL show a toolbar pinned to the top of the view that remains visible while the article scrolls, displaying at its left end a back control that returns the Hub window to the article list, followed by the current mode, a learned-progress counter for the mode, and a text-selection hint. The progress counter SHALL be formatted as `<learned>/<total>`, where `<total>` is the number of lines in the article's content and `<learned>` is the mode's stored progress clamped to that count, so the counter never exceeds the total. The hint SHALL state the selection-to-extract action and render the shortcut key in a visually distinct keycap treatment, distinguishable from the surrounding plain text, and SHALL sit at the toolbar's right end so that no hint element overlaps the article body. When an extraction advances the mode's progress, the counter SHALL update immediately without leaving the practice view. No toolbar control SHALL reveal hidden per-line content in bulk.

#### Scenario: Back control sits at the toolbar's left end
- **WHEN** the practice view renders
- **THEN** the back control is visible at the toolbar's left end, before the mode label, and remains visible while the article scrolls

#### Scenario: Counter shows learned over total
- **WHEN** the practice view opens in a mode whose stored progress is line 12 and the article's content has 50 lines
- **THEN** the toolbar progress counter displays `12/50`

#### Scenario: Stored progress beyond content is clamped
- **WHEN** the practice view opens in a mode whose stored progress is 60 and the article's content has 50 lines
- **THEN** the toolbar progress counter displays `50/50`

#### Scenario: Counter updates immediately after extraction
- **WHEN** an extraction advances the current mode's stored progress from line 12 to line 13
- **THEN** the toolbar progress counter immediately displays `13/<total>` without leaving the practice view

#### Scenario: Empty article content
- **WHEN** the practice view opens for an article whose content has no lines
- **THEN** the toolbar progress counter displays `0/0`

#### Scenario: Hint sits in the toolbar, not over the article
- **WHEN** the practice view renders
- **THEN** the selection hint is visible within the toolbar at its right end, and no hint element covers any part of the article body

#### Scenario: Shortcut key is visually distinct
- **WHEN** the user looks at the selection hint in the toolbar
- **THEN** the shortcut key (`a`) is rendered in a keycap treatment — visually separated from the adjacent hint words, for example by a border and background — rather than as plain inline text

#### Scenario: No bulk reveal control in the toolbar
- **WHEN** the practice view is open in any mode
- **THEN** the toolbar provides no control that shows or hides hidden content for all lines at once

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

### Requirement: Scroll position restore
The system SHALL restore the dialog's scroll position on open to the line stored in the current mode's progress field, and SHALL clamp a stored position that exceeds the article's current line count to the last line. Stored progress SHALL drive learned-line styling: lines at or below the stored position are marked as learned, and a learned line SHALL be rendered with a light gray row background, visibly distinct from the unlearned rows' normal background, with no green or other colored highlight. A learned row SHALL render at the same opacity as any other row — learned styling SHALL NOT reduce opacity. Learned rows SHALL remain fully interactive (toggle, play, selection, and extraction behave as on any other row), and the learned marking SHALL remain observable as a distinct class/state for diagnostics.

#### Scenario: Restore with history
- **WHEN** the dialog opens in Reading mode and `ProgReading` holds line N within the current line count
- **THEN** the view scrolls to line N and lines 1..N are rendered with a light gray row background

#### Scenario: No history
- **WHEN** the dialog opens and the current mode's progress field is 0 or unset
- **THEN** the view starts at the first line with no gray-tinted rows and every line renders at the normal background

#### Scenario: Stored position beyond content
- **WHEN** the stored progress line is greater than or equal to the current line count (for example, after the article was shortened)
- **THEN** the view scrolls to the last line without error

#### Scenario: Learned rows are faded, not green
- **WHEN** any line is marked as learned (on open with stored progress, or immediately after an extract updates progress)
- **THEN** that row is de-emphasized via a light gray background tint distinct from an unlearned row's background, its computed opacity equals an unlearned row's, and its line number uses the normal line-number color

#### Scenario: Learned rows stay interactive
- **WHEN** the user clicks the toggle control, play button, or selects text within a gray-tinted learned row
- **THEN** the control or selection behaves exactly as it does on an unlearned row

#### Scenario: Learned styling perceivable without row text
- **WHEN** the dialog opens in Listening mode where learned rows show no source text until expanded
- **THEN** the learned lines are still distinguishable from unlearned lines by the gray row background alone

### Requirement: Selection capture
The system SHALL capture text selections within the practice view, recording the selected text, its line number (1-based), and the full line text, and expose the selection to the extract command. Deselecting or selecting across nothing SHALL clear the current selection.

#### Scenario: Selection within one line
- **WHEN** the user selects a substring of line 7
- **THEN** the current selection records the selected substring, line number 7, and line 7's full text

#### Scenario: No selection
- **WHEN** the user triggers extraction with no active selection
- **THEN** no extraction occurs and no dialog is opened

### Requirement: Minimize and maximize controls
The Hub window's caption SHALL expose a minimize control and a maximize control, both operating on the window itself. Activating minimize SHALL hide the window to the platform's minimized state without closing it, and the minimized window SHALL be restorable to its previous size and position through the platform's normal window-recovery affordances (taskbar/button or equivalent). Activating maximize SHALL expand the window to fill the screen and SHALL be reversible back to the previous size. Window management actions SHALL NOT write progress, close the window, or disturb the current page — including, on the practice view, the rendered article state (scroll position, revealed lines, current selection).

#### Scenario: Minimize button present and functional
- **WHEN** the user activates the minimize control in the Hub window's caption
- **THEN** the window is minimized rather than closed, no progress is written, and the Hub remains open on its current page

#### Scenario: Minimized dialog is restorable
- **WHEN** the Hub window has been minimized and the user invokes the platform's restore affordance for it
- **THEN** the window reappears with its previous geometry and, when the practice view was showing, with the article scroll position, revealed lines, and selection unchanged

#### Scenario: Maximize and restore
- **WHEN** the user activates the maximize control and then restores the window
- **THEN** the window fills the screen and then returns to its previous size, with all in-window state unchanged

#### Scenario: Window management never writes progress
- **WHEN** the user minimizes, maximizes, or restores the Hub window at any point
- **THEN** the mode's progress field is unchanged, since progress is written only by an extract
