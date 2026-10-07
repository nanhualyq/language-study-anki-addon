## Context

The practice dialog is a single `QDialog` hosting an `AnkiWebView` that renders
one HTML document (`_HTML` in `language_study_anki/practice_dialog.py`) built at
open time from the note's `Content`/`Translation` fields. All four modes share
that document; mode only changes CSS and a few JS branches. Before this change:

- Listening hid `.primary` and Writing hid `.secondary.source`; clicking the
  `.line` row toggled `expanded` / `revealed`, with guards (active selection,
  `.sel-area` hits, a Writing exception) added to stop accidental toggles —
  guards that were incomplete and mode-dependent.
- Reading's `#trans-toggle` flipped a `body.show-trans` class, i.e. a second,
  independent source of truth for visibility.
- Speaking had no hidden content and no reveal path at all.

Selection capture (`computeSel`) and the Ctrl+E extract flow work off the same
rows, so visibility and selection are coupled: hidden text (`display:none`)
cannot be selected, which the extract self-test worked around by injecting the
legacy classes directly.

See proposal.md for the motivation (accidental toggles while selecting text).

## Goals / Non-Goals

**Goals:**

- One explicit, per-line control that reveals/hides hidden content in all four
  modes; touching anything else on the line never changes visibility.
- One visibility state shared by the per-line controls and Reading's toolbar
  toggle, so they cannot disagree.
- Keep text selection, Ctrl+E extraction, TTS, scroll restore, learned styling,
  and the Python bridge contract byte-for-byte compatible.
- Keep the self-test suite (`dialog_modes`, `extract_all_modes`) meaningful:
  it must assert the no-op row click as well as the working control.

**Non-Goals:**

- No change to progress fields, storage format, bridge commands (`lsa:sel:`,
  `lsa:extract`, `lsa:play:`), note types, or extract output.
- No redesign of the toolbar, layout, or typography beyond the new control.
- No per-line "no translation/source exists" indicators (see Risks).
- No mobile/touch-specific affordances beyond what a `<button>` already gives.

## Decisions

**D1 — Real `<button>`, not an HTML `<details>`/`<summary>` element.**
`<details>` looked attractive but the row is a flex container whose
`.sel-area` child must stay a continuous selection target, and `summary`
clicks in Chromium swallow selection start/end in ways that would regress
`computeSel` and the whole extract flow. A real `<button>` still gives
free keyboard activation (Enter/Space), focusability, and `aria-expanded`,
and it can live *outside* the selectable area.
*Alternative rejected:* `<details>` (selection semantics risk), `div` with a
click handler (no keyboard support without extra ARIA work).

**D2 — One boolean class on the row (`.line.open`) is the only CSS hook.**
The per-mode rules map "what is hidden" to "what `.open` reveals":
Listening → `.primary`, Writing → `.secondary.source`, Reading/Speaking →
`.secondary`. This replaces the two legacy classes (`expanded`, `revealed`)
with a single mechanism, so a row is open or closed regardless of mode.
*Alternative rejected:* keeping `expanded`/`revealed` per mode (two code paths
for the same idea, and the toolbar could not drive both).

**D3 — Reading's toolbar toggle drives the same per-row state.**
Instead of a `body.show-trans` class, `#trans-toggle` sets `open` on every
row (open-all when any row is closed, otherwise close-all) and derives its
label from that. One source of truth: after using the toolbar, each row's
chevron agrees with the label.
*Alternative rejected:* keeping `show-trans` and layering a per-row override
(needed a tri-state per row — open/closed/follow-global — and precedence rules
nobody can reason about).

**D4 — Row clicks are an unconditional no-op.**
The old guards (`getSelection().toString()`, `.closest('.sel-area')`, the
Writing exception) existed only to protect a behavior that should not be
invokable by accident. Deleting the toggle removes the need for every guard:
the click handler now dispatches only `[data-twisty]` and `[data-play]`.
Simpler code *and* a property that is trivially testable.

**D5 — Ghost placeholder for rows with nothing hidden.**
When the row's hidden text is empty (empty translation, empty source line,
or a Writing note without translations) the control is not meaningful, so the
row renders an invisible element with the control's width. Consequence: text
stays aligned across every line in every mode.
*Alternative omitted:* always render an active button (clicking it would
visibly do nothing).

**D6 — Speaking reveals the translation on demand.**
Speaking previously showed no translation at all. Giving its control the same
meaning as Reading's ("show this line's translation") keeps one consistent
story across the four modes instead of leaving a dead button in Speaking.

**D7 — Placement: control first, then the optional play button, then text.**
The control is the leftmost element so its position does not depend on whether
the mode has a play button (Listening/Speaking do, Reading/Writing do not).

**D8 — Self-tests click the control, and also prove the row click is inert.**
`_JS_LISTENING` / `_JS_WRITING` / `_JS_SPEAKING` / `_JS_READING` now click
`.line .body` (must not change computed `display`) and then `[data-twisty]`
(must change it); `extract_all_modes` opens the line through the control
before creating the selection range instead of injecting legacy classes —
in Listening the target text is `display:none` until the line is open.

## Risks / Trade-offs

- [Removing the row-click shortcut changes a habit users may already have]
  → Intentional; the control is always visible at a fixed position, and
  Reading's toolbar still opens everything in one click.
- [A `visibility:hidden` ghost could be mistaken for a rendering glitch]
  → It occupies the exact control width, so no layout shift is possible; only
  rows that truly have nothing to reveal get one.
- [Toolbar toggle discards per-row state the user set by hand]
  → Accepted and documented: the toolbar is the "all" action; the label is
  derived from the resulting state so the UI never lies.
- [Pre-existing spec/implementation gap: the Writing scenario promises to
  "indicate none exists when the source has fewer lines", but the dialog has
  always rendered an empty line there, and after this change such rows get a
  ghost (nothing to reveal)] → Out of scope for this change; flagged in the
  final summary so it can be fixed or reworded in a separate change rather
  than silently decided here.
- [Self-test JS runs on a timer inside a real webview (1200 ms after open)]
  → Keep the existing `after_delay` pattern; the assertions only read
  `getComputedStyle`, so no new timing dependency is introduced.
- [QWebEngine's Qt version must support `Array.prototype.some` on a
  NodeList via `Array.prototype.call`] → Long-supported ES5/ES6 features,
  already equivalent to code in this file.

## Migration Plan

No data, schema, or profile migration: the HTML document is regenerated on
every dialog open, so existing notes and progress fields are untouched.
Deploy is the usual `tools/deploy-prod.sh` copy. Rollback = revert the commit
(re-reading the same note renders the old row-click behavior with no residue).

## Open Questions

None blocking. The pre-existing Writing "indicates none exists" gap is a
deliberate non-goal here and is recorded under Risks rather than resolved.
