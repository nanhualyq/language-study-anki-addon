## 1. Page state and badge

- [x] 1.1 In `language_study_anki/web/practice.html`, add script-scope `countPending` + timer state beside `gPending`, a `clearCount()` helper (reset count, hide badge, clear timer), and a static pending-count badge `<span>` in `#toolbar` with CSS matching `.field`; verify by loading the page (syntax check: extract `<script>` content and run `node --check`) and confirming the badge element exists hidden on an empty article
- [x] 1.2 Wire the ~1 s expiry: every digit restarts `clearTimeout` + `setTimeout(clearCount, 1000)`; verify by code walk-through that a lone digit clears state and hides the badge without touching `cur`/`col`

## 2. Keydown branches

- [x] 2.1 Add the digit-intake branch (after the overlay guard and empty-article guard): `1`–`9` start/extend the count, `0` extends only when a count is pending, otherwise falls through to line-start; badge text and timer update on each digit; verify with `node --check` and by the multi-digit scenario (`1`,`0`,`l` = ten columns) in task 4.1
- [x] 2.2 Extend `moveWord(kind)` to accept a count and loop the motion primitive with a stagnation guard (break when a step does not change `col`), pass `±count` through `moveCol(delta)` for `h`/`l`; verify `node --check` and that `99w` at line end is a no-op rather than a loop
- [x] 2.3 Add the `0`/`$` absolute motions as `moveCol(-col)` / `moveCol(len - col)` (so `extendVisual()` and `render()` ride along); verify `node --check` and that `$` then `0` returns to column 0 without changing lines
- [x] 2.4 Add the discard rule: every other key (incl. `j`/`k`/`g`/`G`/PageUp/PageDown/`v`/`Space`/`r`/`a`/`q`) calls `clearCount()` before its existing branch; verify by code walk-through over the whole handler that no branch path leaves a stale count, and that `3` then `j` moves exactly one line

## 3. Keymap overlay

- [x] 3.1 Add the count prefix and `0`/`$` entries to the `#keys` overlay HTML; verify by opening `?` in the running dialog (or reading the template) that both entries are listed and the overlay still toggles closed with `?`

## 4. Self-test coverage

- [x] 4.1 Extend `check_keyboard_nav` in `language_study_anki/selftest_dialog_checks.py` with a count/line-edge probe: `3w` (col advanced three word steps), `1`,`0`,`l` (+10, badge text `10`), `$`/`0` (line end → line start), count + `j` (count discarded, single line move), `v`,`3w` (selection span extended); verify the new assertions pass when the check runs
- [x] 4.2 Add the badge-expiry assertion: badge visible immediately after a digit, then after a >1 s Python-side delay the badge is hidden and the next motion moves one step; verify the assertion passes and does not depend on sub-second timing

## 5. Validation

- [x] 5.1 Run `openspec validate --all` and verify the change passes; then `python -m py_compile language_study_anki/selftest_dialog_checks.py` and `node --check` on the extracted practice.html script
- [x] 5.2 Code walk-through against every scenario in the spec delta (count repeat, multi-digit `0`, line-boundary clamp, line-edge motions, badge expiry, discard by line-level keys, visual extension by count and by `0`/`$`, overlay listing) noting how each is verified; flag any scenario lacking coverage for user decision on running the in-Anki self-test (requires approval per project rules)
