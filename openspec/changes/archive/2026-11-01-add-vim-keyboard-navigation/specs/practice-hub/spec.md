# practice-hub Spec Delta (add-vim-keyboard-navigation)

## ADDED Requirements

### Requirement: List-page keyboard navigation
The system SHALL provide vim-style keyboard navigation on the article-list page. A visible row cursor marks the focused row and a visible skill cursor marks the focused skill entry within that row. `j`/`k` move the row cursor down/up across rows, preserving the skill column; `h`/`l` move the skill cursor left/right across the focused row's four skill entries, wrapping at the edges; `1`–`4` move the skill cursor directly to Reading/Speaking/Listening/Writing. The initial focus is the first row's first skill entry. The focused row and skill SHALL be rendered distinctly from their unfocused state. On an empty list, cursor keys have no effect.

#### Scenario: Row and skill cursor movement
- **WHEN** the user presses `j`, `k`, `h`, `l`, or a digit `1`–`4` on the list page
- **THEN** the row and skill cursors update accordingly, the focused elements are visually distinct, and no other page state changes

#### Scenario: Skill column preserved across rows
- **WHEN** the user moves the skill cursor to the third skill of a row and then presses `j`
- **THEN** the row cursor moves to the next row with the skill cursor on its third skill entry

#### Scenario: Keyboard entry into practice
- **WHEN** the user presses `Enter` or `o` with a skill entry focused
- **THEN** the practice page opens for that row's article and that skill, with the same result as clicking that skill entry, and no progress is written by the navigation

### Requirement: List-page keyboard row actions
The system SHALL expose the list page's article actions on the keyboard. `A` triggers the global add flow with the same result as the Add button. `m` or `.` toggles the focused row's action menu: once open, pressing `m` or `.` again closes it without acting — regardless of whether the menu was opened from the keyboard or the mouse. While the menu is open, `j`/`k` move through its entries and `Enter` activates the focused entry with the same result as clicking it. Menu navigation keys SHALL not affect row or skill cursors while the menu is open. `?` toggles a keymap overlay that lists the page's shortcuts and changes no other page state; pressing `?` again hides it. `Escape` SHALL NOT be bound by the page: Anki injects its own page-level Escape handler (bridge command `close` → `AnkiWebView.onEsc`) that closes the Hub window and cannot be blocked from page script, so page actions must be operable without Escape.

#### Scenario: Global add from the keyboard
- **WHEN** the user presses `A` on the list page
- **THEN** the article-add flow starts, identical to activating the Add button

#### Scenario: Row menu driven from the keyboard
- **WHEN** the user opens a row's action menu with `m`, selects Delete with `j`/`k`, and presses `Enter`
- **THEN** the delete confirmation flow starts for that row's article, identical to clicking the menu's Delete entry, and rows, titles, and percentages are otherwise unchanged

#### Scenario: Second menu key closes the menu
- **WHEN** the user opens a row's action menu with `m` and presses `m` again
- **THEN** the menu closes and no article action is performed

#### Scenario: Menu toggle closes a mouse-opened menu
- **WHEN** the user opens a row's action menu with the mouse and presses `m`
- **THEN** the menu closes, no article action is performed, and the Hub window stays open

#### Scenario: Keymap overlay is non-destructive
- **WHEN** the user presses `?` on the list page
- **THEN** a keymap overlay appears listing the page's shortcuts, and the cursors, menus, rows, and article data are unchanged; pressing `?` again hides it
