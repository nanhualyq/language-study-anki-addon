# practice-dialog Spec Delta (add-vim-keyboard-navigation)

## ADDED Requirements

### Requirement: Line cursor and keyboard movement
The system SHALL provide a vim-style cursor over the practice page's rendered lines: a visible line cursor marks the focused line, and a visible character cursor marks the focused position within that line's primary text. `j`/`k` move the line cursor down/up one line and scroll it into view, preserving the character position within the line; `gg`/`G` move to the first/last line; `h`/`l` move the character cursor one character left/right; `w`/`b`/`e` move the character cursor by words — ASCII word sequences extend as runs, every CJK character counts as its own word, and other non-space characters are single-character words. The initial line cursor position is the first line after the learned progress, or the first line when no progress is stored. Cursor movement SHALL write no progress and SHALL not change line reveal state or the stored selection beyond the cursor's own rendering.

#### Scenario: Cursor movement follows the study position
- **WHEN** the user opens an article with 10 lines and progress 3, then presses `j`
- **THEN** the line cursor starts on line 4 and moves to line 5, scrolled into view, and the progress counter still reads 3/10

#### Scenario: Word motions cross word boundaries
- **WHEN** the character cursor is at the start of a line whose text is "The quick brown fox" and the user presses `w` three times and then `e`
- **THEN** the character cursor visits the starts of "quick", "brown", "fox" and then rests on the last character of "fox"

### Requirement: Keyboard text selection and extract
The system SHALL support selecting text without the mouse. `v` starts a character-wise visual selection at the character under the character cursor — one character wide initially, matching vim, with NO automatic word selection; the motion keys (`w`/`b`/`e`/`h`/`l`) extend it from there. While a visual selection is active, a second `v` cancels it and clears the selection. `V` starts a line-wise visual selection covering the whole focused line. While a visual selection is active, the in-line movement keys (`w`/`b`/`e`/`h`/`l`) extend the selection from its anchor through the character cursor, while line movement (`j`/`k`/`gg`/`G`) cancels an active visual selection and clears it — the selection is confined to a single line, and moving to another line drops it rather than re-selecting the new line. A keyboard-made selection SHALL be indistinguishable from a mouse-made one to every downstream consumer: pressing the existing `a` extract shortcut on it produces the same prefilled note as extracting the same span with the mouse, and the selection participates in the same live-selection updates. `a` CONSUMES the selection: the extract is triggered first and the selection is then cleared, so a second `a` without re-selecting is a no-op — this applies to mouse-made selections too. `a` with no selection remains a no-op. `Escape` SHALL NOT be bound by the page (Anki's injected Escape handler closes the Hub window and cannot be blocked from page script); selection cancellation is the second `v`. In Listening mode, where the primary text is hidden by default, `v`/`V` first reveal the focused line so the selection is visible. Mouse drag-selection and mouse-triggered extract remain unchanged.

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

### Requirement: Keyboard line reveal and playback
The system SHALL operate per-line reveal and TTS playback from the keyboard. `Enter` toggles the focused line's hidden content with the same effect as activating that line's toggle control, in every mode. `p` and `Space` play the focused line's text through the TTS engine in Listening and Speaking modes with the same effect as activating that line's play button; in Reading and Writing modes they have no effect. Reveal and playback keys SHALL write no progress.

#### Scenario: Keyboard reveal matches the toggle control
- **WHEN** the user focuses a closed line in Reading mode and presses `Enter`
- **THEN** that line shows its translation exactly as if its toggle control had been clicked, and other lines are unchanged

#### Scenario: Keyboard playback in Listening mode
- **WHEN** the user focuses a line in Listening mode and presses `p`
- **THEN** that line's text is spoken by the TTS engine, interrupting any playback in progress, as with the line's play button

### Requirement: Keyboard return and keymap help
The system SHALL provide keyboard shortcuts for returning to the list and for discovering the keymap. `q` returns to the article-list page with the same effect as the back control, writing no progress. `?` toggles a keymap overlay listing the practice page's shortcuts; the overlay SHALL not change lines, reveal state, selection, or progress, and pressing `?` again hides it. `Escape` SHALL NOT be bound by the page: Anki injects its own page-level Escape handler (bridge command `close` → `AnkiWebView.onEsc`) that closes the Hub window and cannot be blocked from page script, so every page action must be operable without Escape. The toolbar hint SHALL advertise the keyboard layer.

#### Scenario: Return to list from the keyboard
- **WHEN** the user presses `q` in practice
- **THEN** the article-list page is shown, percentages refresh as with the back control, and no progress was written by the keypress

#### Scenario: Keymap overlay is non-destructive
- **WHEN** the user presses `?` in practice with a visual selection active
- **THEN** the overlay appears, the selection and page state are unchanged, and pressing `?` again dismisses it, restoring the previous view
