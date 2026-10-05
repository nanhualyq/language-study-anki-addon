## MODIFIED Requirements

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
