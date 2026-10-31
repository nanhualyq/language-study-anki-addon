## ADDED Requirements

### Requirement: Article row actions and global add
The article list page SHALL offer three action entries per row — edit,
duplicate-as-new, and delete — alongside the row's skill entries, and one
page-level add entry that is shown whether or not any article exists.
Activating an entry SHALL trigger the corresponding action defined by the
`article-management` capability. The skill entries SHALL remain the only
row entries that navigate to the practice view. After an action's dialog
closes, and after a deletion, the list page SHALL re-render from the
current collection state so rows and percentages reflect the result.

#### Scenario: Row shows action entries
- **WHEN** the list page renders an article row
- **THEN** the row offers edit, duplicate-as-new, and delete entries in
  addition to its four skill entries

#### Scenario: Global add entry is always available
- **WHEN** the list page renders, including when the collection holds no
  articles
- **THEN** the add entry is shown

#### Scenario: Add entry opens the add action
- **WHEN** the user activates the add entry
- **THEN** the add action of `article-management` runs in the same Hub
  window

#### Scenario: Row action opens its dialog
- **WHEN** the user activates the edit, duplicate-as-new, or delete entry of
  a row
- **THEN** the corresponding action of `article-management` runs for that
  row's article, and the skill entries still navigate to practice only

#### Scenario: List refreshes after an action
- **WHEN** an edit or duplicate dialog closes after the user saved or added
  a note, or a deletion completes
- **THEN** the list page is re-rendered from the collection state at that
  moment, with percentages recomputed
