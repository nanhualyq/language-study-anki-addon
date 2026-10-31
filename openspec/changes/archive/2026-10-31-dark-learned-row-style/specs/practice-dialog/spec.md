## MODIFIED Requirements

### Requirement: Scroll position restore
The system SHALL restore the dialog's scroll position on open to the line stored in the current mode's progress field, and SHALL clamp a stored position that exceeds the article's current line count to the last line. Stored progress SHALL drive learned-line styling: lines at or below the stored position are marked as learned, and a learned line SHALL be rendered with a dark gray row background and light-colored text, visibly distinct from the unlearned rows' normal background, with no green or other colored highlight. A learned row SHALL render at the same opacity as any other row — learned styling SHALL NOT reduce opacity. Learned rows SHALL remain fully interactive (toggle, play, selection, and extraction behave as on any other row), and the learned marking SHALL remain observable as a distinct class/state for diagnostics.

#### Scenario: Restore with history
- **WHEN** the dialog opens in Reading mode and `ProgReading` holds line N within the current line count
- **THEN** the view scrolls to line N and lines 1..N are rendered with a dark gray row background

#### Scenario: No history
- **WHEN** the dialog opens and the current mode's progress field is 0 or unset
- **THEN** the view starts at the first line with no dark-tinted rows and every line renders at the normal background

#### Scenario: Stored position beyond content
- **WHEN** the stored progress line is greater than or equal to the current line count (for example, after the article was shortened)
- **THEN** the view scrolls to the last line without error

#### Scenario: Learned rows are faded, not green
- **WHEN** any line is marked as learned (on open with stored progress, or immediately after an extract updates progress)
- **THEN** that row is de-emphasized via a dark gray background distinct from an unlearned row's background and rendered with light-colored text, its computed opacity equals an unlearned row's, and its line number uses the normal line-number color

#### Scenario: Learned-row text stays legible
- **WHEN** a learned row displays its primary text and, when revealed, its secondary text (for example in Reading mode)
- **THEN** the primary text renders white and the secondary text renders a light gray, both legible against the dark learned-row background

#### Scenario: Learned rows stay interactive
- **WHEN** the user clicks the toggle control, play button, or selects text within a dark-tinted learned row
- **THEN** the control or selection behaves exactly as it does on an unlearned row

#### Scenario: Learned styling perceivable without row text
- **WHEN** the dialog opens in Listening mode where learned rows show no source text until expanded
- **THEN** the learned lines are still distinguishable from unlearned lines by the dark row background alone
