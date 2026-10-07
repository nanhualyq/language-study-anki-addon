## MODIFIED Requirements

### Requirement: Scroll position restore
The system SHALL restore the dialog's scroll position on open to the line stored in the current mode's progress field, and SHALL clamp a stored position that exceeds the article's current line count to the last line. Stored progress SHALL drive learned-line styling: lines at or below the stored position are marked as learned, and a learned line SHALL be rendered as a faded row — the entire row (text, line number, and row controls) shown at reduced opacity relative to unlearned rows — with no distinct highlight color or tinted background. Learned rows SHALL remain fully interactive (toggle, play, selection, and extraction behave as on any other row), and the learned marking SHALL remain observable as a distinct class/state for diagnostics.

#### Scenario: Restore with history
- **WHEN** the dialog opens in Reading mode and `ProgReading` holds line N within the current line count
- **THEN** the view scrolls to line N and lines 1..N are rendered as faded (reduced-opacity) rows

#### Scenario: No history
- **WHEN** the dialog opens and the current mode's progress field is 0 or unset
- **THEN** the view starts at the first line with no faded rows and every line renders at full opacity

#### Scenario: Stored position beyond content
- **WHEN** the stored progress line is greater than or equal to the current line count (for example, after the article was shortened)
- **THEN** the view scrolls to the last line without error

#### Scenario: Learned rows are faded, not green
- **WHEN** any line is marked as learned (on open with stored progress, or immediately after an extract updates progress)
- **THEN** that row's computed opacity is lower than an unlearned row's, its background matches the normal row background (no green or other highlight tint), and its line number uses the normal line-number color

#### Scenario: Learned rows stay interactive
- **WHEN** the user clicks the toggle control, play button, or selects text within a faded learned row
- **THEN** the control or selection behaves exactly as it does on an unlearned row
