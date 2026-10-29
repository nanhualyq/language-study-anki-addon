## MODIFIED Requirements

### Requirement: Article list page
The Hub SHALL render an article list page containing one row per note of the Article note type, ordered with the most recently created article first. Each row SHALL display the article's Title and four skill entries — reading, speaking, listening, writing, in that order — each showing that skill's progress percentage for the article. The percentage SHALL be computed as the skill's stored progress line divided by the total number of lines in the article's `Content`, expressed as an integer percentage rounded to the nearest whole number and clamped to 0–100; it SHALL be `0%` when the skill has no progress or `Content` has no lines, and `100%` when the stored progress line reaches or exceeds the line count. When the article has a non-empty `Cover` value, the row SHALL display the cover image at the row's left as a thumbnail constrained to a fixed maximum height while preserving its aspect ratio; a `Cover` value that is empty, absent, or malformed SHALL render as no thumbnail, leaving the row's title and skill entries unchanged. When the collection contains no Article notes, the page SHALL display an empty-state message instead of rows.

#### Scenario: Rows show titles and per-skill percentages
- **WHEN** the Hub opens its list page and the collection contains article notes
- **THEN** each row displays the article's title and four skill percentages matching its stored progress, most recently created article first

#### Scenario: Cover thumbnail shown
- **WHEN** a row's article has a `Cover` value containing an image reference resolvable in the collection media folder
- **THEN** the row displays that image at the left, constrained to the maximum thumbnail height with its aspect ratio preserved

#### Scenario: Empty or absent cover falls back to text-only row
- **WHEN** a row's article has an empty or absent `Cover` value
- **THEN** the row renders with its title and skill entries and no thumbnail, with no placeholder in the thumbnail's place

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
