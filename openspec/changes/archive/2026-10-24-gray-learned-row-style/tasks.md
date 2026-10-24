## 1. Learned-row styling

- [x] 1.1 In `language_study_anki/practice_dialog.py`, replace `.line.learned { opacity: 0.6; }` with `.line.learned { background: #f1f1f2; }` in the inline `_HTML` template, and verify no other `opacity` rule remains for `.learned` (grep the file: only the one rule changed, no JS/Python touched)
- [x] 1.2 Open the dialog in Listening mode on an article with stored progress and verify lines 1..N show a light gray background distinguishable from unlearned lines even though no text is visible, while unlearned lines stay on the normal background (verified via the `learned_style` selftest check on the real dialog webview: learned rows `rgb(241, 241, 242)` vs unlearned `rgba(0, 0, 0, 0)`)
- [x] 1.3 In the same dialog, verify learned rows render at full opacity (text and controls equally crisp as unlearned rows), the line-number color is unchanged, and toggle, play, text selection, and `a` extract all behave normally on a gray-tinted row (verified via `learned_style`: opacity `1` on both, line-number color `rgb(187, 187, 187)` on both, twisty/play/selection on a learned row all captured; extract-on-learned-row covered by `extract_all_modes` since row styling cannot affect the bridge)
- [x] 1.4 Repeat the visual check in Reading mode (gray band on learned lines under visible text) and verify that extracting new text immediately grays the newly learned row via the live update, with the toolbar counter advancing as before (verified via `learned_style`: band under visible primary text, extract at line 20 → progress 20, row 20 gains `.learned` + gray bg live, counter `20/40`)
- [x] 1.5 Open the dialog on an article with no stored progress and verify no row is gray-tinted (verified via `learned_style`: 0 `.learned` rows, row 1 bg `rgba(0, 0, 0, 0)`, counter `0/40`)

## 2. Regression verification

- [x] 2.1 Run the full selftest suite (`LSA_SELFTEST=1 tools/scratch-anki.sh --fresh`) and verify all pre-existing checks still pass alongside `learned_style` (11/11 checks ok)
