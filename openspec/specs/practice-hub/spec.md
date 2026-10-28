# practice-hub Specification

## Purpose

Provides the single entry window for practice: a Tools-menu-opened hub that lists the collection's articles with per-skill progress and navigates between the article list and the practice view defined by the `practice-dialog` capability.

## Requirements

### Requirement: Tools-menu entry
The system SHALL add an item labeled `Language Study: Article List` to Anki's Tools menu. Choosing the item SHALL open the Hub window showing the article list page. Choosing it while a Hub window is already open SHALL raise the existing window to the front and give it focus instead of opening a second Hub window.

#### Scenario: Open the Hub from the Tools menu
- **WHEN** the user chooses `Language Study: Article List` from the Tools menu while no Hub window is open
- **THEN** the Hub window opens showing the article list page

#### Scenario: Repeated choice raises the existing window
- **WHEN** the user chooses the menu item while a Hub window is already open, regardless of which page it shows
- **THEN** the existing Hub window is raised to the front with focus and no second Hub window is created

### Requirement: Article list page
The Hub SHALL render an article list page containing one row per note of the Article note type, ordered with the most recently created article first. Each row SHALL display the article's Title and four skill entries — reading, speaking, listening, writing, in that order — each showing that skill's progress percentage for the article. The percentage SHALL be computed as the skill's stored progress line divided by the total number of lines in the article's `Content`, expressed as an integer percentage rounded to the nearest whole number and clamped to 0–100; it SHALL be `0%` when the skill has no progress or `Content` has no lines, and `100%` when the stored progress line reaches or exceeds the line count. When the collection contains no Article notes, the page SHALL display an empty-state message instead of rows.

#### Scenario: Rows show titles and per-skill percentages
- **WHEN** the Hub opens its list page and the collection contains article notes
- **THEN** each row displays the article's title and four skill percentages matching its stored progress, most recently created article first

#### Scenario: Percentage calculation
- **WHEN** an article has `Content` of 40 lines, `ProgReading` is 10, and `ProgWriting` is 0
- **THEN** its row shows reading at 25% and writing at 0%

#### Scenario: Stored progress beyond content
- **WHEN** an article's stored progress line for a skill exceeds the current line count of its `Content`
- **THEN** that skill's entry shows `100%`

#### Scenario: Empty content
- **WHEN** an article's `Content` is empty
- **THEN** all four of its skill entries show `0%`

#### Scenario: No articles in the collection
- **WHEN** the list page renders and the collection contains no Article notes
- **THEN** the page displays an empty-state message and no rows

### Requirement: List-to-practice navigation
Each skill entry in an article row SHALL be activatable, and activating it SHALL switch the same Hub window to the practice view for that article in that skill's mode; the practice view SHALL render and behave per the `practice-dialog` capability (line rendering, per-line reveal, scroll restore, learned styling, selection capture, extract, TTS). The Hub window title SHALL identify the article list on the list page, and the article's title together with the skill mode on the practice page. Switching from the list to the practice view SHALL NOT write progress.

#### Scenario: Enter practice from a skill entry
- **WHEN** the user activates the reading entry of an article row
- **THEN** the same window switches to the practice view for that article in reading mode and the window title shows the article's title and mode

#### Scenario: Practice view honors stored progress
- **WHEN** the user opens the practice view for an article whose reading progress is stored at line N
- **THEN** the practice view restores to line N per the `practice-dialog` scroll-restore behavior

#### Scenario: Navigation writes no progress
- **WHEN** the user activates a skill entry and the practice view opens
- **THEN** no progress field is written by the navigation itself

### Requirement: Return to list
The practice view SHALL provide a back control at the toolbar's left end that returns the Hub window to the article list page. The list page shown after returning SHALL be re-rendered from the current collection state so that percentages reflect any progress written by extracts made during practice. Returning to the list SHALL NOT write progress.

#### Scenario: Back control returns to the list
- **WHEN** the user activates the back control while the practice view is shown
- **THEN** the window switches back to the article list page

#### Scenario: Percentages refresh after practice
- **WHEN** an extract during practice advanced an article's reading progress and the user then activates the back control
- **THEN** the list page shows the updated reading percentage for that article without reopening the Hub window

#### Scenario: Returning writes no progress
- **WHEN** the user activates the back control at any point during practice
- **THEN** no progress field is written by the return
