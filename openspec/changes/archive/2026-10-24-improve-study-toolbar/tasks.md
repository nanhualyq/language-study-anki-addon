## 1. Toolbar progress counter

- [x] 1.1 In `_HTML` (`practice_dialog.py`), replace the `#pf` textContent (`D.progressField + ':' + D.progress`) with `<learned>/<total>`, where learned is clamped via the same `Math.min(progress, lines.length)` expression used for `learnedTo`. Verify: opening a Reading dialog on a 50-line article with `ProgReading=12` shows `12/50`; stored progress 60 shows `50/50`; empty content shows `0/0` and no error
- [x] 1.2 Extend `window.markLearnedUpTo(n)` to also rewrite the `#pf` text with the newly clamped value. Verify: extract on a line beyond current progress (Python calls `markLearnedUpTo` via `extract.py`) and the counter increments immediately, without reopening the dialog

## 2. Hint relocation and keycap styling

- [x] 2.1 Move the hint into the toolbar as a right-aligned flex item (`margin-left: auto`), delete the fixed-position `.hint` div and its CSS, and wrap the `a` in a `<kbd>` element with a keycap treatment (border + light background, small font). Verify: with the dialog scrolled to the bottom, no element overlaps the article body's bottom-right corner; the `a` renders visibly distinct from the surrounding hint words; the hint stays visible while scrolling in all four modes

## 3. Remove Reading bulk translation toggle

- [x] 3.1 Remove the `#trans-toggle` button markup, its two CSS rules (`#trans-toggle { display: none; }` and `body.mode-reading #trans-toggle { ... }`), and its JS `addEventListener` block including the `openAll` bulk logic. Keep `setOpen` and the `body.mode-* .line.open .secondary` mode rules — the per-row twisties depend on them. Verify: the Reading dialog opens with no toolbar button; clicking a line's twisty still reveals/hides only that line's translation; no JS errors in the web console

## 4. Update the in-addon selftest

- [x] 4.1 Update the Reading-mode check in `selftest_dialog_checks.py` (`_JS_READING` and `_ev_reading`): remove the two `trans-toggle` clicks and the `s1`/`s2` assertions, assert the toolbar toggle is now absent (`toggle: false`), and keep row-click-no-toggle (`s0`, `s0row`) and per-row twisty reveal (`s3`) coverage. Verify: `python -m pytest tests/` still passes (suite does not cover this file — sanity check that no import broke), and running the dialog selftest inside Anki reports the Reading check as ok

## 5. Final verification

- [x] 5.1 Open each of the four practice modes from the Browser and confirm against the spec scenarios: counter shows learned/total and clamps, counter ticks up after an extract, hint sits in the toolbar right end with a keycap `a`, nothing overlaps the article body, and per-line twisty is the only reveal mechanism in every mode
