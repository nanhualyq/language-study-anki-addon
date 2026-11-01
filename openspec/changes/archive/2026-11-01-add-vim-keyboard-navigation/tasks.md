# Tasks — add-vim-keyboard-navigation

## 1. Practice page keyboard layer (`web/practice.html`)

- [x] 1.1 Add cursor state `{cur, col, visual}` and line movement: `j`/`k` move the line cursor with scroll-into-view and `.kcursor` rendering, `gg`/`G` jump to first/last line via a pending-`g` timeout state, initial `cur` = first line after stored progress (fallback line 1); verify in-browser that pressing `j`/`k` walks the highlighted line through an article and writes no progress (counter unchanged)
- [x] 1.2 Add character cursor: `h`/`l` and `w`/`b`/`e` word motions using the D7 word regex (ASCII word runs + CJK runs + single-char punctuation), caret rendered as a `.caret` span measured with `Range.getClientRects()`, col preserved across `j`/`k`; caret rendering is skipped while any DOM selection exists, and `selectionchange` from a mouse drag syncs `cur`/`col`; verify caret moves correctly on a long English line and on a Chinese translation line in Writing mode
- [x] 1.3 Add visual selection: `v` anchors on the word under the cursor, `V` covers the whole line, both realized via `setBaseAndExtent()` on the line's `.primary` text node so the existing `selectionchange` → `lsa:sel` pipeline serves them; motions extend within the line, `j`/`k` move and reselect whole line, `Esc` cancels, `v`/`V` auto-open a closed Listening line first; verify `V` then `a` on a Reading line opens the Add dialog with the full line marked — identical to the mouse drag-select flow
- [x] 1.4 Add reveal/playback keys: `Enter` toggles the focused line through the existing `setOpen` path (same effect as the twisty), `p` and `Space` post `lsa:play:<n>` only in Listening/Speaking modes; verify `Enter` reveals a Reading translation and `p` speaks the focused Listening line, interrupting ongoing TTS
- [x] 1.5 Add `q` (post `lsa:back`), the `?` keymap overlay (fixed-position, non-destructive, dismissed by `?`/`Esc`), update the toolbar hint to advertise `v`/`a`/`?`, and extend the template's top contract comment with the keyboard-layer note; verify `q` returns to the list with percentages refreshed and the overlay leaves selection/progress untouched

## 2. List page keyboard layer (`web/list.html`)

- [x] 2.1 Add cursor state `{row, skill, menu}` with focus rendering: `.krow` on the focused row and `.kskill` on the focused skill (reusing the hover look), `j`/`k` move rows preserving the skill column, `h`/`l` wrap across the row's four skills, `1`–`4` jump directly, initial focus first row first skill, all cursor keys inert on the empty list; verify movement order and wrapping in-browser
- [x] 2.2 Wire activation: `Enter`/`o` post `lsa:open:<id>:<mode>` for the focused (row, skill) — same command as the click path — and `A` posts `lsa:add`; verify Enter opens the expected article+mode and `A` starts the add flow, with no progress written
- [x] 2.3 Add the menu sub-state: `m`/`.` opens the focused row's existing popup, `j`/`k` move within its entries, `Enter` posts the focused entry's `lsa:edit|dup|del:<id>`, `Esc` closes without acting, and row/skill keys are routed to the menu while open; verify Delete-via-keyboard reaches the same confirmation flow as the click path and `Esc` cancels cleanly
- [x] 2.4 Add the `?` keymap overlay and extend the template's top contract comment; verify the overlay toggles without changing rows, menus, or cursors

## 3. Tests

- [x] 3.1 Add static template tests (in `tests/test_hub.py`'s style) asserting both templates contain the keyboard handler and guarded CSS (`.menu-pop[hidden]` rule still present, `<base href="/">` still present, new focus classes referenced); verify with `pytest tests/test_hub.py`
- [x] 3.2 Add self-test keyboard-flow checks to `selftest_dialog_checks.py` that dispatch synthetic `KeyboardEvent`s: list `j`/`l`/`Enter` navigation into practice, practice `V`+`a` extract reaching `extract_log`, `Enter` reveal, `q` back, and an `Esc`-reaches-the-page probe (design risk item); verify the checks pass inside the in-Anki self-test

## 4. Integration verification

- [x] 4.1 Run the full pytest suite (`pytest tests/`) — all existing and new tests pass
- [x] 4.2 Run the in-Anki self-test suite via `tools/scratch-anki.sh` — all checks pass, including the new keyboard checks and the unchanged existing DOM probes
- [x] 4.3 Manual keyboard-only smoke in real Anki: list → `j`/`l`/`Enter` → practice → `V` `a` extract → `Enter` reveal → `q` back; confirm `Esc` behavior on the deployed Anki version, `::selection` visibility on dark `.learned` rows (adjust the page-scoped `::selection` color if low-contrast), and tune the scroll margin per design.md's open question. Resolved across rounds 1–2: Esc deliberately unbound (D11), selection visibility confirmed by the user, scroll margin settled at 56 px, `v`/line-movement semantics per the user's review (5.8/5.9)

## 5. Manual-smoke feedback fixes

Round 1 (caret bar-only + menu sync):
- [x] 5.1 Caret renders bar-only (no character background) so it cannot be mistaken for a selection band (design D4a/risk update)
- [x] 5.2 Sync the list menu sub-state with mouse-opened row menus; self-heal in the render path
- [x] 5.3 Move the practice keydown handler + cursor state outside the empty-article guard so `a`/`?`/`q` work on empty articles (QWebEngine silently swallowed the resulting ReferenceError until jsdom reproduced it)

Round 2 (Escape removal + `v` fixes):
- [x] 5.4 Root-caused Escape: Anki injects `Escape → pycmd("close") → AnkiWebView.onEsc` (closes the QMainWindow) after page scripts; unbind Escape everywhere per user decision — second `v` cancels the visual selection, second `m`/`.` closes the row menu, second `?` closes the overlay (design D9/D11; supersedes the round-1 consume-Escape approach)
- [x] 5.5 Fix `v` on Chinese lines selecting the whole line: every CJK character is its own word (design D7); fix visual-extension off-by-one (inclusive cursor offset used as exclusive range end, dropping the cursor character)
- [x] 5.6 Self-test probes switched to toggle semantics (second-`m` menu close, second-`v` cancel); static test now forbids any Escape binding in either template
- [x] 5.7 Spec deltas updated (toggle cancellation, CJK word model, Escape-unbound requirements + scenarios) and design.md records D7/D9/D11 with the root-cause analysis
- [x] 5.8 `v` restored to vim semantics per user review: starts collapsed on the cursor character (one char, NO automatic word selection — that was an unwarranted `viw` shortcut); word picks come from `v`+`e`/`w`. Selftest probe asserts `v` → 1-char selection and second-`v` cancellation; overlay/spec/design wording updated
- [x] 5.9 Line movement (`j`/`k`/`gg`/`G`) now CANCELS an active visual selection instead of re-selecting the new line wholesale (user behavior; single-line extract contract). Spec scenario flipped ("Line movement cancels a visual selection"), selftest probes V→j cancel then k→V→a extract
- [x] 5.10 `a` consumes the selection (user review): extract fires first (Python captures the selection synchronously in `run_extract`; bridge delivers in order), then the highlight is cleared — no stray double-extract; applies to mouse-made selections too (design D12, spec scenario "Extract consumes the selection", selftest acancel probe)
