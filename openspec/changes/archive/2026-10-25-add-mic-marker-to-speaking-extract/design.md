## Context

`field_builder.build_front(lines, line_number, start, end, …)` assembles the
extract `Front` field: up to 3 context lines, then the selected line with
`[start:end]` wrapped in `<mark>`, then a hidden timestamp span.
`extract.py` calls it once per mode; Speaking currently passes no highlight
replacement, producing `<mark>text</mark>` — identical in shape to Reading.
The `Back` for Speaking is the raw selected text (`sel["text"]`), and the
hidden-timestamp / dedup-defeat behavior must not change. See proposal.md
for motivation.

## Goals / Non-Goals

**Goals:**
- Speaking `Front` renders the marked selection as `<mark>🎤text🎤</mark>`.
- Zero output change for reading, writing, listening (regression-guarded).
- `Back`, `Phone`, lookup, progress, and the hidden timestamp untouched.

**Non-Goals:**
- Distinguishing writing from reading (both stay plain `<mark>`).
- Any migration of already-extracted notes.
- Card-template or browser-column changes.

## Decisions

- **D1 — Decoration inside the mark.** `🎤` goes inside `<mark>` per the
  requested format. Alternative considered: `🎤<mark>text</mark>🎤`
  (keeps the highlight visually clean) — rejected; inside-the-mark is more
  prominent in the browser's rendered Front and was the explicit request.
- **D2 — Generic parameters on `build_front`.** Add optional
  `mark_prefix: str = ""` and `mark_suffix: str = ""`; defaults keep every
  existing call byte-identical. `build_front` stays the single owner of
  mark assembly (it already owns `<mark>` wrapping and escaping). Alternatives:
  building the emoji into the caller's string — impossible, since the caller
  doesn't control the mark segment; a single `mark_emoji` param that echoes
  the emoji on both sides — rejected as less flexible for trivial savings.
- **D3 — Mode knowledge stays in `extract.py`.** Module constants
  `_SPEAKING_MARK_PREFIX = _SPEAKING_MARK_SUFFIX = "🎤"`; the speaking
  branch passes them, all other branches pass nothing (or the defaults).
  `field_builder` never learns what "speaking" means.
- **D4 — Decoration is concatenated, not escaped.** The emoji values are
  code constants, not user input; escaping them would be a no-op for the
  emoji but sets a wrong precedent. `html.escape` continues to apply only to
  article-derived text, unchanged.
- **D5 — Self-test via extract-log token.** Following the established
  `EXTRACT_ROUNDS` pattern, the extract log gains a `mark:mic` token in the
  `kinds` string when speaking, and the speaking round requires it. This
  matches how the other mode behaviors are asserted (log tokens), without
  reaching into the Add dialog's note content.
- **D6 — No migration (confirmed).** Only extracts after the change carry
  the 🎤. Old `@EnSpeak` notes keep plain `<mark>`; acceptable cosmetic
  inconsistency, fully reversible by re-extraction.

## Risks / Trade-offs

- [Old and new speaking notes coexist in the collection → browser lists show
  mixed styles] → Accepted (D6); the note type still identifies them
  uniformly, and `Front:🎤` simply returns only new ones.
- [`🎤` inside `<mark>` picks up the highlight color] → Cosmetic only;
  emoji remain legible on the default card templates' `<mark>` background.
- [Answer comparison during review: Front shows `🎤text🎤`, Back shows
  `text`] → The decoration is visually peripheral; Back intentionally stays
  clean so it matches the Youdao lookup input and phonetics.
- [Adopted foreign `@EnSpeak` note types] → Unaffected: the change is
  field *content*, not templates or fields; provisioning's field-repair
  path is untouched.

## Migration Plan

Deploy = normal addon copy + Anki restart (`tools/deploy-prod.sh`). No data
migration, no collection changes on load. Rollback = revert the code; notes
extracted in the interim simply keep their 🎤 (harmless plain text in
`Front`).

## Open Questions

None — placement, scope, and migration were resolved in exploration.
