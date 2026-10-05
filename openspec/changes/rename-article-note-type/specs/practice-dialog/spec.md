## MODIFIED Requirements

### Requirement: Browser context-menu entry
The system SHALL add a context-menu item group to the Browser table menu for selected article notes, offering "Practice: Listening", "Practice: Speaking", "Practice: Reading", and "Practice: Writing". The items SHALL appear only when the selection consists of article notes.

#### Scenario: Right-click an article note
- **WHEN** the user right-clicks a note of the `LSA-Article` note type in the Browser
- **THEN** the context menu contains the four practice items, and choosing one opens the practice dialog for that article in the chosen mode

#### Scenario: Right-click a non-article note
- **WHEN** the user right-clicks a note that is not of the `LSA-Article` note type
- **THEN** no practice items are shown
