## Context

Today the only entry into practice is the Browser context menu
(`browser_menu.py`) opening `PracticeDialog` — a QDialog hosting one
AnkiWebView fed from `web/practice.html`, keyed per (note, mode) so several
practice dialogs can coexist. The reference Flutter app instead opens on an
article list with per-skill progress and navigates into practice pages with
a back affordance. This change ports that entry model: one Hub window,
opened from the Tools menu, swapping a new list page and the existing
practice page inside a single webview. See proposal.md for motivation; the
behavioral contract lives in the `practice-hub` delta and the modified
`practice-dialog` requirements.

## Goals / Non-Goals

**Goals:**
- One window, two pages (list <-> practice) in a single AnkiWebView, swapped
  via `setHtml`; navigation through two new bridge commands.
- Keep every practice-page behavior (rendering, reveal, restore, selection,
  extract, TTS, D8 no-write-on-close) intact inside the Hub.
- Keep `open_dialog(parent, note_id, mode)` working as an adapter so the
  existing selftest checks drive the practice page with minimal edits.
- Remove the Browser context-menu entry and its module.

**Non-Goals:**
- CRUD in the list (edit / delete / save-as / reset progress): Anki's
  Browser owns note management; the list is a practice launcher only.
- Multiple simultaneous practice pages: the Hub shows one article+mode at a
  time (deliberate loss, recorded in the proposal).
- Practice-page state persistence across navigation: returning to the list
  discards the practice DOM; re-entering re-renders (scroll/learned state
  recover from progress fields, per the existing restore requirement).
- Deck/note-type provisioning changes; extraction flow changes; TTS changes.

## Decisions

- **D1 — Single window, two pages (QDialog + one AnkiWebView).** Chosen over
  a list dialog + separate practice dialogs: the user asked for "switch to
  the study view" with a back-to-list control, and a stack of windows makes
  "back" mean window juggling. The Hub stays a QDialog with the
  minimize/maximize flags already proven in `practice_dialog.py` (same
  caption-button pattern as aqt/models.py).
- **D2 — Page swap by `setHtml`, not QStackedWidget with a Qt list.** One
  rendering stack (HTML + bridge), list re-render on back gives progress
  refresh for free, and the selftest harness already drives pages via
  `runJavaScript` probes. Alternative — native Qt list widget — rejected:
  two UI stacks in one window, and list checks would need a different
  harness than the existing dialog checks.
- **D3 — Two new bridge commands.** `lsa:open:<note_id>:<mode>` from list
  rows; `lsa:back` from the toolbar back control. The practice contract
  (`lsa:sel:`, `lsa:extract`, `lsa:play:<n>`, `markLearnedUpTo`) is
  unchanged. Python routes on current page state: `lsa:open` re-renders the
  practice payload into the same webview; `lsa:back` re-renders the list
  from a fresh `col.find_notes` + progress read.
- **D4 — Refactor PracticeDialog into Hub + page logic.** The window class
  moves to a new `hub.py` (`HubWindow`), singleton-keyed globally (module
  `_hub` ref, cleared on close) instead of the per-(note,mode) `_open` dict.
  The practice-page logic (payload build, bridge dispatch for sel/extract/
  play, TTS, `markLearnedUpTo`) is extracted so `HubWindow` composes it.
  `open_dialog(parent, nid, mode)` in `practice_dialog.py` becomes a thin
  adapter: opens/raises the Hub and switches to that article's practice
  page — selftest checks and extract.py's `dialog.web` /
  `dialog.selection` / `dialog._article` / `dialog._lines` /
  `dialog._translations` / `dialog.mode` access patterns keep working
  because the Hub instance exposes the same attributes.
- **D5 — List template `web/list.html`.** Read once at import like
  `practice.html` (missing file = deploy error at startup). Payload:
  `__LSA_DATA__` JSON with rows `[{id, title, pcts: {reading, speaking,
  listening, writing}}]`. Percent helper (`_progress_percent`) moves from
  `browser_menu.py` into hub-side code unchanged in behavior — the
  practice-hub spec's percentage rules are identical to the removed
  context-menu rules.
- **D6 — Toolbar back control lives in `practice.html`.** Left-end `<`
  button calling `lsa:back`, before the mode label; spec requirement
  updated accordingly. The list page needs no toolbar. Window title is set
  from Python per page: list page → `Language Study`, practice page →
  `<mode label> — <title>` (existing behavior).
- **D7 — Menu registration.** `mw.form.menuTools` QAction
  "Language Study: Article List" registered in `__init__.init()` in place of
  `browser_menu.register()`; the bootstrap idempotence guard covers
  re-registration on addon reload. Guard against `mw.col is None` (no
  profile open) with a tooltip, same spirit as provisioning_ui's check.

## Risks / Trade-offs

- [Only one practice page at a time — behavior loss vs. today's per-(note,
  mode) dialogs] → Accepted deliberately; recorded in the proposal and in
  the singleton Hub requirement. Power users re-entering a second article
  lose the first article's unsaved-in-DOM state, but progress lives in
  note fields, so nothing durable is lost.
- [Selftest churn: `check_browser_menu` and any context-menu assertions
  break by design] → Replace with Hub list-page checks (open via menu
  action or `open_dialog`, probe DOM for rows/percentages, exercise
  `lsa:open`/`lsa:back`); the other 6 dialog checks ride the adapter
  unchanged. Tasks include a harness run to confirm.
- [`setHtml` swap resets the webview; a stale `lsa:play`/`lsa:extract` JS
  callback arriving after a swap hits the wrong page] → Bridge dispatch
  validates current page state (selection/extract ignored unless the
  practice page is active; `lsa:open`/`lsa:back` ignored in mismatched
  state), matching the existing try/except-and-log pattern.
- [Closing the Hub mid-extract: Anki's native Add dialog is parented to mw,
  not the Hub] → No change from today's dialog flow; extract completion
  only calls `markLearnedUpTo` on `dialog.web`, and a missing/destroyed
  webview is wrapped in the existing exception guard.
- [List reads the whole collection on every render] → Article notes are
  few (study material); `find_notes('note:LSA-Article')` + per-note field
  reads are cheap at this scale. No index or cache needed.

## Migration Plan

Pure in-addon refactor; no data migration. Deploy = normal addon copy +
restart (tools/deploy-prod.sh). Rollback = reinstall previous addon
version; collections are untouched (note types, fields, suspension all
unchanged). Spec archive: `practice-hub` becomes a new main spec;
`practice-dialog` delta merges (context-menu requirement removed, toolbar
and window requirements replaced).

## Open Questions

- Menu label exact wording (`Language Study: Article List`) is fixed in the
  hub spec; revisit only if the user prefers a different label — a
  one-line spec + code tweak.
