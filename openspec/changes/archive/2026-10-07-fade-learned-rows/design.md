## Context

Learned-row styling lives entirely in the inline `<style>` block of the `_HTML` template in `language_study_anki/practice_dialog.py`:

```css
.line.learned { background: #f2f9f2; }
.line.learned .ln { color: #4a4; }
```

The `learned` class itself is applied by the template's JS (initial render and `window.markLearnedUpTo`), and the selftest (`selftest_dialog_checks.py`) probes `document.querySelectorAll('.line.learned').length` — it never asserts colors. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- Learned rows visually recede: whole row rendered at reduced opacity.
- Green tint (background + line-number color) removed.
- No change to class application, scroll restore, extract flow, or selftest probes.

**Non-Goals:**
- No dark-mode work (the dialog uses a fixed light palette today).
- No rework of progress tracking or the `markLearnedUpTo` live-update path.
- No accessibility audit beyond keeping controls functional.

## Decisions

1. **Fade with CSS `opacity` on `.line.learned`** — the user explicitly asked for whole-row opacity reduction ("降低整行的透明度"). `opacity` dims text, line numbers, borders, and row controls uniformly and composites cleanly over the `#fafafa` page background.
   - Alternatives: alpha-blended text/background colors (only touches painted colors, not controls, and requires picking new colors per element — more values to tune); `filter: opacity(...)` (equivalent effect, less conventional). Rejected both.

2. **Opacity value: `0.6`** as the default. Noticeably faded while body text (`#222`) stays legible at dialog font sizes. The user did not pin a value; it is one constant in one rule, trivially tunable later. Spec only requires learned rows to be *lower* than unlearned, so the exact number is not load-bearing.

3. **Delete the green rules rather than override them** — remove `background: #f2f9f2` and the `.ln` color override; the `.line.learned` rule carries only `opacity`. This guarantees no residual tint and keeps a single source of truth for the learned look.

4. **Keep the `learned` class and all JS untouched** — the class remains the observable marker for the selftest and for `markLearnedUpTo`; only presentation changes.

## Risks / Trade-offs

- [Faded rows slightly harder to read at 0.6] → Mitigation: keep body text at full-contrast `#222` and tune the single opacity constant if the user finds it too faint (e.g. raise to 0.7).
- [Row controls (twisty, play) on learned rows also look dimmed, which can read as "disabled"] → Accepted: user asked for a whole-row fade; controls remain fully functional (opacity does not affect hit-testing) and hover feedback still works.
- [Existing green could be assumed by other checks] → Mitigation: grepped repo — only the two CSS rules reference the green values; selftest asserts class counts, not colors.

## Migration Plan

Single-file CSS edit; no data or schema changes. Rollback = restore the two removed rules.

## Open Questions

- Exact opacity level (default 0.6) — tunable without affecting the spec or task breakdown.
