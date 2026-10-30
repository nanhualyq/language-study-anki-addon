## MODIFIED Requirements

### Requirement: Minimize and maximize controls
The Hub window's caption SHALL expose a minimize control and a maximize control, both operating on the window itself. Activating minimize SHALL hide the window to the platform's minimized state without closing it, and the minimized window SHALL be restorable to its previous size and position through the Hub window's own platform window entry (taskbar button or equivalent). Activating maximize SHALL expand the window to fill the screen and SHALL be reversible back to the previous size. Window management actions SHALL NOT write progress, close the window, or disturb the current page — including, on the practice view, the rendered article state (scroll position, revealed lines, current selection).

#### Scenario: Minimize button present and functional
- **WHEN** the user activates the minimize control in the Hub window's caption
- **THEN** the window is minimized rather than closed, no progress is written, and the Hub remains open on its current page

#### Scenario: Minimized dialog is restorable
- **WHEN** the Hub window has been minimized and the user invokes the restore affordance for the Hub's own platform window entry
- **THEN** the window reappears with its previous geometry and, when the practice view was showing, with the article scroll position, revealed lines, and selection unchanged

#### Scenario: Maximize and restore
- **WHEN** the user activates the maximize control and then restores the window
- **THEN** the window fills the screen and then returns to its previous size, with all in-window state unchanged

#### Scenario: Window management never writes progress
- **WHEN** the user minimizes, maximizes, or restores the Hub window at any point
- **THEN** the mode's progress field is unchanged, since progress is written only by an extract
