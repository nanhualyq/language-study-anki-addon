## 1. CSS change in the practice dialog template

- [x] 1.1 In `language_study_anki/practice_dialog.py`, replace the two green learned rules (`.line.learned { background: #f2f9f2; }` and `.line.learned .ln { color: #4a4; }`) with a single `.line.learned { opacity: 0.6; }` rule, then verify `grep -n "f2f9f2\|#4a4" language_study_anki/practice_dialog.py` returns nothing and `grep -n "line.learned" language_study_anki/practice_dialog.py` shows only the opacity rule
- [x] 1.2 Confirm no JS changes were made: the `learned` class application in the initial render and `window.markLearnedUpTo` still exist unchanged (`grep -n "classList.add('learned')\|' learned'" language_study_anki/practice_dialog.py` shows both)

## 2. Verification

- [x] 2.1 Run the unit suite and confirm it passes: `python -m unittest discover -s tests -t .`
- [x] 2.2 In Anki, run the addon selftest (dialog restore stage 4.3) and confirm it still passes — it asserts `.line.learned` counts and scroll restore, which must be unaffected by the styling change
- [x] 2.3 Manually open a practice dialog on an article with stored progress and verify per the spec scenarios: lines 1..N render faded (computed opacity < 1) with no green/tinted background and normal line-number color, unlearned lines render at full opacity, and the toggle/play controls and text selection still work on a faded row
- [x] 2.4 Extract a new line mid-session and verify the newly learned row fades live via `markLearnedUpTo` (opacity applied immediately, no reload)
