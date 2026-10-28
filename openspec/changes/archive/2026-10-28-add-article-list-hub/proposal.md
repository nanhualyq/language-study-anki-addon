## Why

Practice is currently reachable only by right-clicking an article note in the
Anki Browser — there is no overview of what to study or how far along each
article is. The reference Flutter app opens on an article list with per-skill
progress; Anki users need the same "pick an article, pick a skill" entry,
plus a way back to the list without reopening the Browser.

## What Changes

- Add a Hub window: one AnkiWebView that swaps between a new **article list
  page** (title + four per-skill progress buttons per row) and the existing
  **practice page**, so choosing a skill switches into practice and a
  top-left **back control** returns to the list (list re-renders, progress
  percentages refresh).
- Register a top-level entry in Anki's **Tools menu** that opens the Hub
  (singleton: repeated clicks raise the existing window).
- **BREAKING**: remove the Browser context-menu entry and its
  `browser_menu.py` module; the Tools-menu Hub becomes the only entry point.
  The reusable per-skill progress-percentage helper moves into the Hub code.
- Keep `open_dialog(parent, note_id, mode)` as a thin adapter that opens the
  Hub directly on the given article's practice page (selftest and any direct
  callers keep working).
- Practice behavior (rendering, per-line reveal, selection capture, extract,
  TTS, scroll restore, D8 no-write-on-close/back) is unchanged inside the
  Hub's practice page.
- Adjust `practice-dialog` requirements: drop the Browser-menu requirement,
  phrase the toolbar/window requirements for the Hub window (back control in
  the toolbar's left end).

## Capabilities

### New Capabilities

- `practice-hub`: the Hub window — Tools-menu entry, singleton lifetime,
  article list page (rows with per-skill progress buttons), list-to-practice
  and practice-to-list navigation, list refresh on return, empty-list state.

### Modified Capabilities

- `practice-dialog`: remove the "Browser context-menu entry" requirement
  (replaced by the Hub entry); update the toolbar requirement to include the
  back control at the toolbar's left end and reframe window-management
  requirements for the Hub window; all other requirements (rendering, reveal
  control, scroll restore, selection capture) continue to apply to the
  practice page inside the Hub.

## Impact

- `language_study_anki/browser_menu.py` — deleted.
- `language_study_anki/practice_dialog.py` — practice logic reused by the Hub;
  `open_dialog` becomes a Hub adapter.
- New `language_study_anki/hub.py` (window + list data) and
  `language_study_anki/web/list.html` (list template).
- `language_study_anki/web/practice.html` — toolbar gains a back control;
  bridge contract gains `lsa:open:<nid>:<mode>` and `lsa:back`.
- `language_study_anki/__init__.py` — register Hub menu instead of
  browser_menu.
- `language_study_anki/selftest_dialog_checks.py` — replace the
  `browser_menu` check with Hub list-page checks; other checks keep driving
  the practice page via the adapter.
- README entry-point description; `practice-dialog` main spec updated on
  archive.
- Behavioral loss: only one practice page lives in the Hub at a time
  (previously multiple per-note practice dialogs could be open simultaneously).
