## MODIFIED Requirements

### Requirement: Keyboard shortcut triggers extraction
The system SHALL provide a `Ctrl+E` shortcut in the practice dialog that sends the current selection to Anki's Add dialog. The shortcut SHALL have no effect when no selection exists. When a required note type or deck is missing, the shortcut SHALL first obtain the user's confirmation to create it; declining cancels the extraction.

#### Scenario: Shortcut with active selection
- **WHEN** the user has a selection in the practice view and presses `Ctrl+E`
- **THEN** Anki's Add dialog opens with a prefilled note as specified below

#### Scenario: Shortcut without selection
- **WHEN** the user presses `Ctrl+E` with no active selection
- **THEN** nothing happens: no dialog opens and no note is constructed

#### Scenario: Missing note types declined during extraction
- **WHEN** the user presses `Ctrl+E` while required note types or decks are missing and declines the creation confirmation
- **THEN** extraction is cancelled: no Add dialog opens and no note is constructed
