## ADDED Requirements

### Requirement: Independent top-level window
The Hub window SHALL be an independent top-level window that is not owned by Anki's main window, so that the platform presents it as its own window — with its own taskbar button or the platform's equivalent window entry — separate from the main Anki window's entry. A Hub window that is open while the Anki profile closes or Anki quits SHALL be closed as part of that shutdown, and closing the Hub window at any time SHALL NOT write progress.

#### Scenario: Separate platform window entry
- **WHEN** the Hub window is open while the main Anki window is also open
- **THEN** the platform shows a separate window entry (taskbar button or equivalent) for the Hub, distinct from the main Anki window's entry, and activating it raises or restores the Hub

#### Scenario: Minimized Hub restorable from its own entry
- **WHEN** the Hub window has been minimized and the user invokes the platform's restore affordance for the Hub's own window entry
- **THEN** the window reappears with its previous geometry and, when the practice view was showing, with the article scroll position, revealed lines, and selection unchanged

#### Scenario: Profile shutdown closes the Hub
- **WHEN** the user closes the open profile or quits Anki while the Hub window is open
- **THEN** the Hub window is closed as part of the shutdown and no progress is written by that closing
