## 1. Per-line reveal control (practice_dialog.py `_HTML`)

- [x] 1.1 Render an explicit toggle control as the first element of every line,
      using an invisible same-width placeholder on lines with nothing hidden in
      the current mode — verify: extracted dialog HTML for all four modes shows
      `<button class="twisty" data-twisty="1">` on line 1 (ghost on lines whose
      hidden text is empty) and every line's text keeps the same left indent.
- [x] 1.2 Replace the legacy visibility rules (`expanded`, `revealed`,
      `body.show-trans`) with a single `.line.open` hook plus per-mode reveal
      targets — verify: computed `display` of the hidden element is `none` on a
      closed row and non-`none` on an open row in Listening, Writing, Reading
      and Speaking (browser evaluation against the extracted HTML).
- [x] 1.3 Add the `setOpen` helper (toggles the class, the chevron glyph and
      `aria-expanded`) and wire the control's click handler — verify: clicking
      the control flips only that row, the glyph changes `▸`/`▾`, and
      `aria-expanded` flips `false`/`true`.
- [x] 1.4 Delete row-click toggling and its selection guards so a click on the
      row body or its text is a pure no-op — verify: clicking `.line .body`
      before and after a text selection changes no computed `display` in any of
      the four modes.
- [x] 1.5 Make Reading's `#trans-toggle` drive the same per-row state and derive
      its label from it — verify: with any row closed the button opens every row
      and reads "Hide translation"; a second press closes every row and reads
      "Show translation", and individual chevrons agree with the label.
- [x] 1.6 Confirm Speaking reveals the translation line through its control —
      verify: computed `display` of `.secondary` goes `none` → visible after one
      click, while the source text and play button stay untouched.

## 2. Self-test coverage

- [x] 2.1 Update `_JS_READING`, `_JS_LISTENING`, `_JS_WRITING`, `_JS_SPEAKING`
      and their `_ev_*` evaluators to assert both the inert row click and the
      working control — verify: `python -m unittest discover -s tests -t .`
      still passes and the four JS payloads parse (each is built from plain
      string concatenation in `selftest_dialog_checks.py`).
- [x] 2.2 Update the `extract_all_modes` reveal step to open the line through
      the control instead of injecting the removed `expanded`/`revealed`
      classes — verify: the JS references `[data-twisty]` and no longer contains
      `classList.add('expanded')`.
- [x] 2.3 Run the in-Anki suite —
      `LSA_SELFTEST=1 LSA_SELFTEST_KEEP=1 tools/scratch-anki.sh` — and verify
      `.scratch-anki/selftest-results.json` reports `ok: true` for
      `dialog_modes` and `extract_all_modes` (all ten checks green).

## 3. Verification and cleanup

- [x] 3.1 Reconcile the pre-existing working-tree diff with this plan: review
      `git diff language_study_anki/` and either keep it as the implementation
      of 1.1–1.6 / 2.1–2.2 or adjust it — verify: `git diff` contains no
      changes outside `practice_dialog.py` and `selftest_dialog_checks.py`.
- [x] 3.2 Manual pass in the scratch instance: open all four modes, reveal and
      hide lines with the control, select text across a line, press Ctrl+E, and
      play TTS — verify: selection and extraction behave as before and no
      reveal/hide happens while selecting.
- [x] 3.3 Check the main spec docs for stale row-click wording — verify:
      `rg -i "click the line|row click|expanded" README.md openspec/specs/`
      returns nothing that contradicts the new per-line control.
