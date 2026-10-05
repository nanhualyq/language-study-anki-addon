## Context

`provisioning.provision(col)` creates all six items idempotently
(resolve-by-name → create-if-missing), but its only normal-user call site is
the extract flow (`extract.py`), nothing asks the user first, and one of the
items — the `Articles` deck — has zero runtime consumers. Design decision D7
of the original change deferred provisioning to first use, "not at addon
load"; this change revises that to a two-stage, confirmation-gated flow and
drops the article deck entirely. See proposal.md for motivation; the spec
text being changed lives in `openspec/specs/article-storage/spec.md`
(Auto-provisioning; Articles never enter the review queue) and
`openspec/specs/practice-extract/spec.md` (Ctrl+E precondition).

Constraints:

- `init()` runs before a profile/collection exists — `mw.col` is unavailable
  there, so "at load" is impossible; profile open is the earliest hook with a
  collection.
- `tests/` run under a system interpreter without `aqt`; any module imported
  by tests (and `provisioning.py` itself) must stay import-clean without Anki.
- The self-test harness (`LSA_SELFTEST`) is headless: a modal dialog it
  cannot answer would stall it until the watchdog fires.

## Goals / Non-Goals

**Goals:**

- A fresh install yields the `LSA-Article` note type after profile open + one
  confirmation — no need to read field lists out of the source.
- Extract targets (`@Basic`, `@EnListen`, `@EnSpeak`, `English`) are created
  at first extraction, behind the same kind of confirmation.
- No collection mutation without user consent, ever.
- One shared "confirm + create" path used by both stages.

**Non-Goals:**

- Creating or requiring an `Articles` deck — removed, see D6.
- Remembering a "never ask" preference across sessions (a config flag for a
  dialog that stops appearing after one acceptance is over-engineering).
- Provisioning at addon `init()` time (no collection exists yet).
- Changing what the extract target types contain (same fields, same
  adopt-by-name rules).

## Decisions

**D1 — Startup trigger: `gui_hooks.profile_did_open` (supersedes D7).**
Alternatives: (a) keep lazy-only — rejected, the article type stays
invisible without reading code; (b) provision silently at startup — rejected,
mutates the collection without consent; (c) `mw.runTimer` /
`appstateDidChange` — no advantage over `profile_did_open`, which fires
exactly once per profile open with `mw.col` ready. The self-test already
uses this hook, proving it is safe for modal UI.

**D2 — Two scopes, one confirm-and-provision helper.**
`provisioning.py` gains a pure `missing_items(col, scope)` — scope
`"article"` → the `LSA-Article` note type; scope `"extract"` → the three
extract note types plus deck `English` — and keeps `provision(col)` as the
full idempotent entry used by the self-test. The new UI module
`provisioning_ui.py` exposes
`ensure_provisioned(col, parent, *, scope, context)`: compute missing → if
empty return the provisioning result silently → else one
`QMessageBox.question` listing exactly the missing items → accept: provision
that scope and return the result; decline: return `None`. Startup calls it
with `scope="article"`; `extract.py` calls it with `scope="extract"` and
shows a short info message and returns before `col.new_note` on `None`.
Alternatives: duplicating the dialog at both call sites — rejected, drift
risk; putting the dialog in `provisioning.py` — rejected, breaks the
aqt-free import contract; provisioning everything at startup — rejected,
defeats the requested staging.

**D3 — Self-test auto-accepts.** When `LSA_SELFTEST` is set,
`ensure_provisioned` skips the dialog and provisions. The harness has no way
to click a modal; the existing startup-dialog dismisser only targets known
first-run dialogs. Normal users never see this path (env-gated).

**D4 — Decline is not persisted; re-offer cadence follows the stage.**
Declined at startup → offered again at the next profile open (the article
scope has no other creation point). Declined at extract → offered again at
the next extraction. After acceptance the condition never recurs
(idempotent), so at most one dialog per stage ever succeeds. Rationale:
decline state in `meta.json`/config adds a silent way to get permanently
stuck without the types; re-offering is cheap.

**D5 — Dialog content is data-driven.** The message is built from
`missing_items()` output, so adopted-but-present items are never listed and
the user sees precisely what will change. English strings, matching existing
UI copy (`Practice: …`, `Article content is empty`).

**D6 — Drop the `Articles` deck entirely.** Evidence: the only references
are `provisioning.py` itself (creates it, returns `article_deck_id`) and the
self-test (places test article notes there); no runtime code reads, moves, or
validates article deck residence, and suspension alone (`queue = -1`) is what
keeps articles out of review. Alternatives: keep creating it — rejected, a
dead item that pollutes the confirmation dialog; keep the spec's "dedicated
article deck" clause unenforced — rejected, a spec that lies.
Consequences: remove the `ARTICLE_DECK` constant, its creation, and the
`article_deck_id` return key; the "Articles never enter the review queue"
spec requirement loses its deck clause; the self-test's five references
retarget to an existing deck; README drops "dedicated deck".

## Risks / Trade-offs

- [Modal on profile open delays startup] → shown only when `LSA-Article` is
  missing; once ever per collection, then never again.
- [Two dialogs on a fresh profile (startup + first extract)] → accepted
  trade-off of the requested staging; each dialog lists only its own items,
  so neither is surprising.
- [Self-test regression from deck removal] → task group 2 retargets all five
  references; the suite is re-run as verification (task 6.3).
- [Anyone relying on the spec'd dedicated deck] → nothing enforced it before
  either (article notes are hand-created into any deck); spec and README now
  describe reality.
- [First-run Anki dialogs (language chooser) interplay] → `profile_did_open`
  fires after the profile finishes loading; D3 removes the confirm dialog
  from the harness path entirely.
- [`col.decks.by_name` API drift across Anki versions] → target is Anki
  26.8.1+ only (README), where the API is stable.
- [Spec/behavior drift until archive] → this change's delta specs carry the
  new contract; sync happens via the normal archive flow.
