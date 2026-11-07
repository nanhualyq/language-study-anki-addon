## MODIFIED Requirements

### Requirement: Line cursor and keyboard movement
The system SHALL provide a vim-style cursor over the practice page's rendered lines: a visible line cursor marks the focused line, and a visible character cursor marks the focused position within that line's primary text. `j`/`k` move the line cursor down/up one line and scroll it into view, preserving the character position within the line; `gg`/`G` move to the first/last line; `PageUp`/`PageDown` move the line cursor by one screen at a time — the view scrolls one usable screen and the cursor follows onto the edge of the new screen it reads from next (the first visible line after `PageDown`, the last fully visible line after `PageUp`; vim `Ctrl-F`/`Ctrl-B` parity), and when the view cannot scroll further in that direction (the article's edge, or an article that fits on one screen) they scroll nothing and move no cursor; `h`/`l` move the character cursor one character left/right; `w`/`b`/`e` move the character cursor by words — ASCII word sequences extend as runs, every CJK character counts as its own word, and other non-space characters are single-character words. The in-line motions `h`/`l`/`w`/`b`/`e` accept a numeric count prefix: digits `1`–`9` begin a count, further digits (including `0`) extend it while a count is pending (`10l`), and the motion then repeats that many times; repetition SHALL stop at the line's boundaries so a count never moves the character cursor off the current line. Bare `0` (no count pending) moves the character cursor to the start of the line, and `$` moves it to the end of the line; both are absolute positions, take no count, and never leave the line. While a count is pending the practice view SHALL display it as a visible badge, and the pending count SHALL expire about one second after the last digit, clearing the badge without moving anything. Any key that is neither a digit nor one of `h`/`l`/`w`/`b`/`e` SHALL discard the pending count and then behave exactly as it does without one — in particular `j`/`k`/`gg`/`G`/`PageUp`/`PageDown` move by one step or one screen regardless of a pending count. The initial line cursor position is the first line after the learned progress, or the first line when no progress is stored. Cursor movement SHALL write no progress and SHALL not change line reveal state or the stored selection beyond the cursor's own rendering.

#### Scenario: Cursor movement follows the study position
- **WHEN** the user opens an article with 10 lines and progress 3, then presses `j`
- **THEN** the line cursor starts on line 4 and moves to line 5, scrolled into view, and the progress counter still reads 3/10

#### Scenario: Page keys scroll with the cursor
- **WHEN** the user opens an article longer than one screen and presses `PageDown`, then `PageUp`
- **THEN** the view advances one screen with the line cursor landing on the new screen's first visible line, `PageUp` brings the view back one screen with the cursor landing on that screen's last fully visible line, and at the article's top or bottom edge the keys scroll nothing and move no cursor

#### Scenario: Word motions cross word boundaries
- **WHEN** the character cursor is at the start of a line whose text is "The quick brown fox" and the user presses `w` three times and then `e`
- **THEN** the character cursor visits the starts of "quick", "brown", "fox" and then rests on the last character of "fox"

#### Scenario: Count repeats an in-line motion
- **WHEN** the character cursor is at the start of a line and the user presses `3w`
- **THEN** the character cursor lands where three successive `w` presses would land, in one keystroke, still on the same line

#### Scenario: Multi-digit count swallows the `0`
- **WHEN** the user presses `1`, then `0`, then `l`
- **THEN** the `0` extends the pending count instead of moving to the line start, and `l` moves the character cursor ten characters to the right (clamped at the line end)

#### Scenario: Count never leaves the line
- **WHEN** the character cursor is on a line shorter than the count and the user presses `99l` (or `99b`)
- **THEN** the character cursor stops at that line's end (or start) and remains on the same line

#### Scenario: Line-edge motions
- **WHEN** the character cursor sits mid-line and the user presses `$`, then `0`
- **THEN** the character cursor first jumps to the end of the line and then back to the start of the line, without changing lines or scrolling

#### Scenario: Pending count is visible and expires
- **WHEN** the user presses `3`, sees the pending-count badge, and then waits about a second without pressing another digit
- **THEN** the badge disappears without any movement, and the next `w` moves the character cursor one word rather than three

#### Scenario: Line-level keys discard a pending count
- **WHEN** a count is pending and the user presses `j`
- **THEN** the pending count is discarded, its badge clears, and the line cursor moves down exactly one line

### Requirement: Keyboard text selection and extract
The system SHALL support selecting text without the mouse. `v` starts a character-wise visual selection at the character under the character cursor — one character wide initially, matching vim, with NO automatic word selection; the motion keys (`w`/`b`/`e`/`h`/`l`) extend it from there. While a visual selection is active, a second `v` cancels it and clears the selection. `V` starts a line-wise visual selection covering the whole focused line. While a visual selection is active, the in-line movement keys (`w`/`b`/`e`/`h`/`l`) extend the selection from its anchor through the character cursor, while line movement (`j`/`k`/`gg`/`G`/`PageUp`/`PageDown`) cancels an active visual selection and clears it — the selection is confined to a single line, and moving to another line drops it rather than re-selecting the new line. A count prefix applies to those extensions exactly as it does to plain cursor movement — `v` then `3w` extends through three word motions in one keystroke — and `0`/`$` extend the selection to the line's start/end; the pending-count badge, its expiry, and the discard rules are identical while a selection is active. A keyboard-made selection SHALL be indistinguishable from a mouse-made one to every downstream consumer: pressing the existing `a` extract shortcut on it produces the same prefilled note as extracting the same span with the mouse, and the selection participates in the same live-selection updates. `a` CONSUMES the selection: the extract is triggered first and the selection is then cleared, so a second `a` without re-selecting is a no-op — this applies to mouse-made selections too. `a` with no selection remains a no-op. `Escape` SHALL NOT be bound by the page (Anki's injected Escape handler closes the Hub window and cannot be blocked from page script); selection cancellation is the second `v`. In Listening mode, where the primary text is hidden by default, `v`/`V` first reveal the focused line so the selection is visible. Mouse drag-selection and mouse-triggered extract remain unchanged.

#### Scenario: Whole-line extract from the keyboard
- **WHEN** the user presses `V` then `a` on a line in Reading mode
- **THEN** the extract opens the prefilled Add dialog with that entire line marked as the selection — the same result as drag-selecting the whole line with the mouse and pressing `a`

#### Scenario: Partial-line extract with word motions
- **WHEN** the user presses `v` with the cursor inside a word, extends the selection with `e`, and presses `a`
- **THEN** the extract opens the prefilled Add dialog with exactly the selected span marked, including the character the cursor rests on, matching a mouse selection of the same span

#### Scenario: `v` starts on the cursor character, not a word
- **WHEN** the user presses `v` with the cursor inside a word of a Chinese or English line
- **THEN** exactly the one character under the cursor becomes the selection — the surrounding word is NOT auto-selected — and a following `e` extends it through the end of that word

#### Scenario: Line movement cancels a visual selection
- **WHEN** the user presses `V` (or `v` with extensions) and then `j`
- **THEN** the selection is cleared, the line cursor moves to the next line keeping its character position, and pressing `a` performs no extraction

#### Scenario: Extract consumes the selection
- **WHEN** the user presses `V` then `a`, waits for the prefilled Add dialog, and presses `a` again after it closes
- **THEN** the first `a` opens the Add dialog for the selected line as before, the selection highlight is gone once the keys are processed, and the second `a` performs no extraction and writes no progress

#### Scenario: Canceling a visual selection
- **WHEN** the user presses `v` and then `v` again
- **THEN** the visual highlight disappears and pressing `a` performs no extraction

#### Scenario: Listening mode auto-reveals for selection
- **WHEN** the user presses `V` on an unopened line in Listening mode
- **THEN** that line reveals its source text and the whole line becomes the active selection

#### Scenario: Count extends a visual selection
- **WHEN** the user presses `v` with the cursor inside a word and then `3w`
- **THEN** the selection spans from the anchor through the character cursor exactly as three separate `w` presses would, in one keystroke

#### Scenario: Line-edge keys extend a visual selection
- **WHEN** the user presses `v` mid-line and then `$`
- **THEN** the selection grows from its anchor through the end of the line; when the anchor lies after the cursor, pressing `0` instead grows it back to the start of the line, always covering the anchor through the cursor character

### Requirement: Keyboard return and keymap help
The system SHALL provide keyboard shortcuts for returning to the list and for discovering the keymap. `q` returns to the article-list page with the same effect as the back control, writing no progress. `?` toggles a keymap overlay listing the practice page's shortcuts, including the count prefix and the `0`/`$` line-edge motions; the overlay SHALL not change lines, reveal state, selection, or progress, and pressing `?` again hides it. `Escape` SHALL NOT be bound by the page: Anki injects its own page-level Escape handler (bridge command `close` → `AnkiWebView.onEsc`) that closes the Hub window and cannot be blocked from page script, so every page action must be operable without Escape. The toolbar hint SHALL advertise the keyboard layer.

#### Scenario: Return to list from the keyboard
- **WHEN** the user presses `q` in practice
- **THEN** the article-list page is shown, percentages refresh as with the back control, and no progress was written by the keypress

#### Scenario: Keymap overlay is non-destructive
- **WHEN** the user presses `?` in practice with a visual selection active
- **THEN** the overlay appears, the selection and page state are unchanged, and pressing `?` again dismisses it, restoring the previous view

#### Scenario: Keymap lists count and line-edge motions
- **WHEN** the user presses `?`
- **THEN** the overlay lists the count prefix (digits before a motion) and the `0`/`$` line-edge keys alongside the existing shortcuts
