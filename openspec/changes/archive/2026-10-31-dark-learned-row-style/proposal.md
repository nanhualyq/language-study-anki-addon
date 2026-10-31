## Why

Learned rows in the practice view are currently tinted `#f1f1f2` against a `#fafafa` page — a 9/255 difference that users report as "not clearly distinct" (the original request: 换个设计，比如黑底白字). The light-gray band was chosen by the previous `gray-learned-row-style` change when row-level opacity was rejected; it is too faint to read at a glance, especially in Listening mode where closed learned rows carry no text at all and the band is the only signal.

## What Changes

- Restyle learned rows from a light gray band (`#f1f1f2`) to a **dark gray band (`#333`) with light text**: primary text renders white, secondary (translation) text renders `#bbb`, and per-row controls (twisty, its hover/open states) get light-on-dark colors so they stay visible and don't flash white on hover.
- Line numbers keep their existing color (`#bbb`), which remains legible on `#333` and preserves the current spec scenario (learned and unlearned rows share the line-number color).
- Row opacity stays at 1 (the dark background is a background color, not the `opacity` property — the existing "learned styling SHALL NOT reduce opacity" constraint is kept).
- Update the selftest `check_learned_style` expectations: the expected background constant changes from `rgb(241, 241, 242)` to `rgb(51, 51, 51)`, plus a new assertion pinning the learned row's primary text color to white.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `practice-dialog`: the learned-row rendering requirement changes from "light gray row background" to "dark gray (`#333`) row background with light-colored text"; all surrounding constraints (no opacity reduction, no colored highlight, unchanged line-number color, interactivity, perceivable without text, `learned` class observability) are retained.

## Impact

- `language_study_anki/web/practice.html` — the `.line.learned` rule plus child-color overrides (`.primary`, `.secondary`, `.twisty` incl. hover/open states).
- `language_study_anki/selftest_dialog_checks.py` — `check_learned_style` expected-color constants and assertions.
- `openspec/specs/practice-dialog/spec.md` — learned-styling requirement and related scenarios (via this change's delta spec).
- No data model, bridge command, storage, or Python-side behavior changes; `.scratch-anki/` remains a deploy target only.
