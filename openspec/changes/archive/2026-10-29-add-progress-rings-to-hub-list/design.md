# Design: add-progress-rings-to-hub-list

## Context

The list page (`web/list.html`) is a self-contained template injected into a
QWebEngine view; `hub.py` replaces `__LSA_DATA__` with
`{rows:[{id,title,cover,pcts:{...}}]}`. Skill entries are `<button class="skill">`
whose text is `"<Skill> <pct>%"`, wired to `pycmd('lsa:open:<id>:<mode>')`.
Two contracts pin the current text format:

1. `tests/test_hub.py` asserts the exact JS literal
   `"esc(LABELS[m]) + ' ' + pct + '%</button>'"`.
2. `selftest_dialog_checks.py` (`check_hub_list`) probes live DOM via
   `querySelectorAll('.skill')` → `s.textContent` and compares to
   `f"{label} {pct}%"` (and later updates an expectation to
   `"Reading 100%"` after an extract).

See proposal.md - Why. Percentage computation, payload, and bridge are
unchanged; this is a presentation change with two pinned contracts.

## Goals / Non-Goals

**Goals:**
- Render each skill entry as a Flutter-style circular progress ring: arc
  length encodes the percentage, integer percent centered in the ring, skill
  name below, whole cell still clickable.
- Single accent color for all arcs; magnitude alone distinguishes entries.
- Keep the self-test suite green by updating both pinned contracts in the
  same change.

**Non-Goals:**
- No change to percentage math, payload shape, bridge commands, or navigation.
- No per-state colors, gradients, or heatmap semantics.
- No dark-mode work (page stays light-themed as today).
- No ring animations or hover morphing beyond the existing hover background.

## Decisions

### D1 SVG ring via stroke-dasharray, not conic-gradient
`<svg viewBox="0 0 36 36">` with two `<circle>` elements at `r=15.5`
(circumference C = 2*pi*15.5 ~ 97.39), `stroke-width: 3`, group rotated -90
degrees so the arc starts at 12 o'clock (Flutter convention). The value arc
sets `stroke-dasharray = C` and `stroke-dashoffset = C * (1 - pct/100)`
(clamped to [0, C]). Alternatives: conic-gradient needs a radial mask to make
a ring and gives no stroke joins; a canvas is heavier. SVG renders crisply at
40px in QWebEngine's Chromium with no dependency.

### D2 Single accent color (user decision)
Arc `#3b82f6` on track `#e3e3e5`, centered percent text `#555`, name `#666`.
No amber/green state coloring - the user explicitly chose magnitude-by-arc
with one accent. All values legible on the existing `#fafafa`/`#fff` light
page.

### D3 Entry structure keeps the button as the click target
```
<button class="skill" data-open="<id>:<mode>">
  <span class="ring">
    <svg viewBox="0 0 36 36"> track circle + value circle </svg>
    <span class="pct">42%</span>
  </span>
  <span class="name">Reading</span>
</button>
```
`.ring` is `position: relative`; `.pct` is absolutely centered over the SVG
(HTML span, not SVG text - consistent font, simpler styling). The delegated
`[data-open]` click handler is untouched, so the whole cell stays
activatable (spec: list-to-practice navigation). Button chrome changes from
horizontal pill to a small vertical cell (~44px tall); hover keeps a subtle
background tint.

### D4 Percent text moves out of the button textContent (deliberate contract
break)
The self-test probe switches from whole-button `textContent` to
`.pct` and `.name` sub-element reads, and its expected values split into
per-part strings (plus the post-extract update). The probe is the addon's
own diagnostic, so both ends move in the same change; noted as the primary
risk below.

### D5 Static test asserts the new shape
`test_hub.py`'s old format-string assertion is replaced by assertions that
the template contains the ring markup, the `stroke-dashoffset` computation,
and the `.pct`/`.name` spans - i.e. assert what the template must keep
producing, not the old literal.

## Risks / Trade-offs

- [Selftest check turns red if probe and template drift] -> D4: update both
  in the same task group; run the selftest afterwards.
- [1% arc is sub-pixel and nearly invisible] -> accepted: reads as "barely
  started"; the centered number disambiguates.
- [Absolute positioning inside buttons can be finicky in QWebEngine] -> keep
  `.ring` a plain inline-block; verify visually in the scratch instance.
- [Row height grows slightly] -> acceptable; rows already flex.

## Open Questions

- None blocking. The accent `#3b82f6` is a default the user can retune
  cosmetically without a spec change.
