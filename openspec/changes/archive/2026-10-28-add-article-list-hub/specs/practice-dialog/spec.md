## REMOVED Requirements

### Requirement: Browser context-menu entry
**Reason**: The Tools-menu Hub window (`practice-hub` capability) replaces the Browser context menu as the entry point for practice; keeping both would duplicate entry paths and menu maintenance.
**Migration**: Open practice via Tools > `Language Study: Article List`, pick the article row and skill entry in the list page. The per-skill progress percentages formerly shown in the context-menu labels now appear on each list row.

## MODIFIED Requirements

### Requirement: Toolbar progress counter and selection hint
The practice view SHALL show a toolbar pinned to the top of the view that remains visible while the article scrolls, displaying at its left end a back control that returns the Hub window to the article list, followed by the current mode, a learned-progress counter for the mode, and a text-selection hint. The progress counter SHALL be formatted as `<learned>/<total>`, where `<total>` is the number of lines in the article's content and `<learned>` is the mode's stored progress clamped to that count, so the counter never exceeds the total. The hint SHALL state the selection-to-extract action and render the shortcut key in a visually distinct keycap treatment, distinguishable from the surrounding plain text, and SHALL sit at the toolbar's right end so that no hint element overlaps the article body. When an extraction advances the mode's progress, the counter SHALL update immediately without leaving the practice view. No toolbar control SHALL reveal hidden per-line content in bulk.

#### Scenario: Back control sits at the toolbar's left end
- **WHEN** the practice view renders
- **THEN** the back control is visible at the toolbar's left end, before the mode label, and remains visible while the article scrolls

#### Scenario: Counter shows learned over total
- **WHEN** the practice view opens in a mode whose stored progress is line 12 and the article's content has 50 lines
- **THEN** the toolbar progress counter displays `12/50`

#### Scenario: Stored progress beyond content is clamped
- **WHEN** the practice view opens in a mode whose stored progress is 60 and the article's content has 50 lines
- **THEN** the toolbar progress counter displays `50/50`

#### Scenario: Counter updates immediately after extraction
- **WHEN** an extraction advances the current mode's stored progress from line 12 to line 13
- **THEN** the toolbar progress counter immediately displays `13/<total>` without leaving the practice view

#### Scenario: Empty article content
- **WHEN** the practice view opens for an article whose content has no lines
- **THEN** the toolbar progress counter displays `0/0`

#### Scenario: Hint sits in the toolbar, not over the article
- **WHEN** the practice view renders
- **THEN** the selection hint is visible within the toolbar at its right end, and no hint element covers any part of the article body

#### Scenario: Shortcut key is visually distinct
- **WHEN** the user looks at the selection hint in the toolbar
- **THEN** the shortcut key (`a`) is rendered in a keycap treatment — visually separated from the adjacent hint words, for example by a border and background — rather than as plain inline text

#### Scenario: No bulk reveal control in the toolbar
- **WHEN** the practice view is open in any mode
- **THEN** the toolbar provides no control that shows or hides hidden content for all lines at once

### Requirement: Minimize and maximize controls
The Hub window's caption SHALL expose a minimize control and a maximize control, both operating on the window itself. Activating minimize SHALL hide the window to the platform's minimized state without closing it, and the minimized window SHALL be restorable to its previous size and position through the platform's normal window-recovery affordances (taskbar/button or equivalent). Activating maximize SHALL expand the window to fill the screen and SHALL be reversible back to the previous size. Window management actions SHALL NOT write progress, close the window, or disturb the current page — including, on the practice view, the rendered article state (scroll position, revealed lines, current selection).

#### Scenario: Minimize button present and functional
- **WHEN** the user activates the minimize control in the Hub window's caption
- **THEN** the window is minimized rather than closed, no progress is written, and the Hub remains open on its current page

#### Scenario: Minimized dialog is restorable
- **WHEN** the Hub window has been minimized and the user invokes the platform's restore affordance for it
- **THEN** the window reappears with its previous geometry and, when the practice view was showing, with the article scroll position, revealed lines, and selection unchanged

#### Scenario: Maximize and restore
- **WHEN** the user activates the maximize control and then restores the window
- **THEN** the window fills the screen and then returns to its previous size, with all in-window state unchanged

#### Scenario: Window management never writes progress
- **WHEN** the user minimizes, maximizes, or restores the Hub window at any point
- **THEN** the mode's progress field is unchanged, since progress is written only by an extract
