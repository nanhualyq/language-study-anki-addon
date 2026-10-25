## Context

`format_phonetics()` in `language_study_anki/youdao.py` is the single point
where Youdao phonetics become the `Phone` field string; its only consumer is
the extract flow (`extract.py`), which writes it for `@EnListen`/`@EnSpeak`
notes. The project spec (practice-extract) already mandates `<br>` — never
raw newlines — as the inter-line separator inside field values, because Anki
field content is HTML and card rendering collapses raw `\n` to a space.
See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- `Phone` carries one phonetic per line, `<br>`-separated, rendered as
  distinct lines in Anki's editor and on any card template that includes
  `{{Phone}}`.
- Keep the change confined to the formatting function, its test, and the
  spec delta.

**Non-Goals:**
- Rendering `{{Phone}}` in provisioned card templates (separate concern;
  provisioning is additive-fields-only and never patches existing note
  types' templates).
- Rewriting `Phone` on notes already saved with the old single-line format.

## Decisions

1. **`<br>` as the separator** (chosen) vs raw `\n` (rejected: violates the
   spec's separator rule and collapses to a space in card HTML) vs keeping
   spaces (status quo, rejected by request). `<br>` is the only option that
   actually renders multi-line in both the Add-dialog editor and the
   reviewer.
2. **Format inside `format_phonetics()`**, not at a later render layer:
   it is the sole formatting choke point and there is exactly one consumer,
   so deferring the decision would add a layer with no beneficiary.
3. **Deliberate divergence from "Flutter parity"**: the reference app joined
   with spaces. The docstring and the unit test
   (`test_format_phonetics_flutter_parity`) currently enshrine parity; both
   are updated so a future parity audit does not silently revert this.
4. **No migration of existing notes**: extraction only ever writes new
   notes; old notes keep their single-line `Phone`. Rewriting user notes
   for a cosmetic format would be disproportionate risk.

## Risks / Trade-offs

- [Old notes stay single-line, collection shows mixed formats] → Accepted;
  purely cosmetic, only new extractions change.
- [`<br>` visible as literal text if a Phone value is ever consumed by a
  non-HTML consumer] → No such consumer exists today; noted for future
  field consumers.
- [Single-region or missing phonetics edge cases] → `join` naturally
  yields a plain single line / empty string; covered by scenarios in the
  delta spec.
