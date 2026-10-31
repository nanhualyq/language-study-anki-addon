## 1. Learned-row styling (practice.html)

- [x] 1.1 In `language_study_anki/web/practice.html`, replace the `.line.learned` rule with `background: #333` and add learned-row overrides: `.primary` → `#fff`, `.secondary` → `#bbb`, `.twisty` → `#aaa`, `.line.open .twisty` → `#eee`, `.twisty:hover` background → `#4a4a4a`; leave `.ln` and `.play` untouched; update the CSS comment (keep the "no opacity property" rationale, change "light gray band" wording to dark) — verify by re-reading the style block that every light-on-dark override from design.md decision 3 is present and no other rule targets `.line.learned`

## 2. Selftest expectations

- [x] 2.1 In `language_study_anki/selftest_dialog_checks.py` `check_learned_style`: change `GRAY = "rgb(241, 241, 242)"` to the dark constant `rgb(51, 51, 51)`, rename the `live_gray` key/comments to match the dark styling, and add an assertion that the learned row's `.primary` computed color is `rgb(255, 255, 255)` — verify by re-reading the function that background-difference, opacity-equality, line-number-equality, live-restyling, and reset assertions are all still present

## 3. Verification

- [x] 3.1 Run `LSA_SELFTEST=1 LSA_SELFTEST_KEEP=1 tools/scratch-anki.sh`, then check `.scratch-anki/selftest-results.json` reports `"learned_style": {"ok": true, ...}` and no other check flipped to failing
- [x] 3.2 In the kept-open scratch Anki, open an article's practice view with stored progress: confirm learned rows render as dark `#333` bands with white primary text (Reading mode), solid dark bands in Listening mode's closed rows, twisty hover shows no white flash, and selection + extract on a learned row still work
