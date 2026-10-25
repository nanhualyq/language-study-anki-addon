## ADDED Requirements

### Requirement: Minimize and maximize controls
The practice dialog's window caption SHALL expose a minimize control and a maximize control, both operating on the practice dialog itself. Activating minimize SHALL hide the dialog to the platform's minimized state without closing it, and the minimized dialog SHALL be restorable to its previous size and position through the platform's normal window-recovery affordances (taskbar/button or equivalent). Activating maximize SHALL expand the dialog to fill the screen and SHALL be reversible back to the previous size. Window management actions SHALL NOT write progress, close the dialog, or disturb the rendered article state (scroll position, revealed lines, current selection).

#### Scenario: Minimize button present and functional
- **WHEN** the user activates the minimize control in the practice dialog's caption
- **THEN** the dialog is minimized rather than closed, no progress is written, and the dialog remains registered as open for its note and mode

#### Scenario: Minimized dialog is restorable
- **WHEN** the practice dialog has been minimized and the user invokes the platform's restore affordance for it
- **THEN** the dialog reappears with its previous geometry and with the article scroll position, revealed lines, and selection unchanged

#### Scenario: Maximize and restore
- **WHEN** the user activates the maximize control and then restores the dialog
- **THEN** the dialog fills the screen and then returns to its previous size, with all in-dialog state unchanged

#### Scenario: Window management never writes progress
- **WHEN** the user minimizes, maximizes, or restores the practice dialog at any point
- **THEN** the mode's progress field is unchanged, since progress is written only by an extract
