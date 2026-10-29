# Proposal: add-progress-rings-to-hub-list

## Why

Hub list skill entries render progress as plain text (`Reading 42%`); 0%, partial,
and 100% look identical, so the user cannot scan which articles/skills are done,
started, or untouched. A circular progress ring (Flutter-style) encodes magnitude
visually: empty ring = not started, arc = partial, full ring = done.

## What Changes

- Replace each list-row skill entry's text percentage with a circular progress
  ring (~40px): a filled arc proportional to the percentage over an unfilled
  track, the integer percentage centered inside the ring, the skill name below
  it.
- All rings use a single accent color (`#3b82f6` arc on `#e3e3e5` track) — no
  status/heatmap coloring; magnitude is carried by arc length alone. `0%`
  renders an empty track, `100%` a complete ring.
- Entries remain `<button>` elements sending `lsa:open:<note_id>:<mode>`;
  the bridge contract, list payload, and percentage computation are unchanged.
- Update the self-test hub list probe (`selftest_dialog_checks.py`) to read the
  new per-entry DOM (`.name` / `.pct`) instead of whole-button `textContent`,
  and its expected skill strings accordingly.
- Update the static template assertions in `tests/test_hub.py` that pin the
  old `"Reading 42%"` button markup.
- Update the contract comment at the top of `web/list.html`.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `practice-hub`: the Article list page requirement gains the ring rendering
  contract (arc proportional to percentage, number centered, name below, single
  accent color, empty/full ring at 0%/100%); percentage computation and all
  existing scenarios are unchanged.

## Impact

- `language_study_anki/web/list.html` — markup, CSS, and ring-building JS only
- `language_study_anki/selftest_dialog_checks.py` — hub list DOM probe and
  expected strings (runtime self-test contract)
- `tests/test_hub.py` — static template assertions
- `openspec/specs/practice-hub/spec.md` — via this change's delta
- Unchanged: `hub.py` payload/bridge, `_progress_percent`, practice view,
  navigation, progress writes
