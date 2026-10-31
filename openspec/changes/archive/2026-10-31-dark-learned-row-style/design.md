## Context

Learned rows are styled by a single rule in `language_study_anki/web/practice.html` (`.line.learned { background: #f1f1f2; }`). All other colors in the row are chosen for the light page (`body` background `#fafafa`): primary text inherits `#222`, secondary is `#666`, line number `.ln` is `#bbb`, twisty is `#888` (hover `#ececec` background, open `#444`), play button is a white pill with `#bbb` border. The spec (`practice-dialog` → Scroll position restore) currently mandates "light gray row background", no opacity reduction, unchanged line-number color, full interactivity, and perceptibility without text (Listening mode).

The selftest `check_learned_style` in `language_study_anki/selftest_dialog_checks.py` pins `GRAY = "rgb(241, 241, 242)"`, asserts learned-vs-unlearned background difference, equal row opacity, equal line-number color, live restyling after extract, and clear-on-reset. Motivation and scope: see proposal.md.

## Goals / Non-Goals

**Goals:**
- Make learned rows unmistakable at a glance in all four modes, including Listening mode's textless closed rows.
- Keep every existing constraint: row opacity unchanged, line-number color unchanged, controls fully interactive, no colored (green) highlight, learned state still observable via class.
- Keep selftest `check_learned_style` green with updated expectations, so the design stays pinned by regression.

**Non-Goals:**
- No transition/animation on the restyle (consistent with the rest of the page, which has none).
- No changes to the list page (`list.html`), hub, bridge commands, progress storage, or Python-side logic.
- No theme system or per-mode variations of the learned style.

## Decisions

**1. Dark gray `#333` background (chosen with the user), not pure black and not `rgba(0,0,0,0.9)`.**
The user's original idea was "black background + white text + 0.1 transparency". Explore surfaced that "0.1 transparency" is ambiguous: as opacity 0.1 it reproduces the current faintness (and makes white text unreadable); as 10% transparency it means near-solid black. A solid `#333` was selected as the agreed middle ground: strong contrast on the light page without the harshness of `#000`. Solid color over alpha keeps the computed style trivially assertable (`rgb(51, 51, 51)`) and free of background-blending surprises.

**2. Background color only — never the `opacity` property.**
The spec forbids learned styling from reducing opacity (a faded row is an empty row in Listening mode, and opacity would also dim the row's own text tint). `background` with an opaque color sidesteps this entirely; the constraint text stays unchanged.

**3. Child elements get explicit light-on-dark overrides on learned rows.**
`.primary` → `#fff` (inherits `#222`, invisible on dark otherwise); `.secondary` → `#bbb` (≈6.6:1 on `#333`); `.twisty` → `#aaa`, open → `#eee` (the normal `#444` open color is invisible on dark), twisty hover background → `#4a4a4a` (the normal `#ececec` would flash a white block on the dark row). Alternatives considered: applying a CSS `filter: invert()` to the whole row (would also invert the selection highlight and any future child styling — rejected as too blunt), and overriding colors via a wrapper class on text only (leaves controls unreadable — rejected).

**4. Line number `.ln` and play button stay untouched.**
`#bbb` on `#333` remains legible (≈6.6:1) and less prominent than body text, preserving the spec scenario that learned and unlearned rows share the line-number color — this keeps the existing selftest assertion intact. The white play button reads fine as a control on the dark row.

**5. Selftest updates ride along.**
`check_learned_style` swaps its expected constant to `rgb(51, 51, 51)` and gains one assertion pinning the learned row's primary text color to white (the new spec scenario "Learned-row text stays legible"). Background-difference, opacity-equality, line-number-equality, live-restyling, and reset assertions keep their current shape.

## Risks / Trade-offs

- [Dark rows dominate the view once an article is mostly learned] → Accepted: that is the requested signal; `#333` (not `#000`) limits the weight, and unlearned rows below the fold are unaffected.
- [White selection highlight on dark rows might read differently than on light rows] → Chromium's default selection overlay remains visible on `#333`; the selftest exercises selection on a learned row, so regressions are caught.
- [Spec/selftest drift if hex values are duplicated in several places] → Hex lives in exactly two places (the template rule and the selftest constant); both are updated in the same task and verified by running the check.
- [`.scratch-anki/` copy diverging from the source tree] → Never edited by hand; `tools/scratch-anki.sh` re-syncs before selftest runs.
