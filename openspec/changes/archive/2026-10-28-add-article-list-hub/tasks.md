## 1. Hub window and list page

- [x] 1.1 Create `language_study_anki/hub.py` with a singleton `HubWindow` (QDialog, minimize/maximize caption flags, 920x720, one AnkiWebView, module-level `_hub` ref cleared on close) and verify a scratch Anki instance can open it empty with no errors
- [x] 1.2 Move the `_progress_percent` helper out of `browser_menu.py` into hub-side pure code and verify it with the same edge cases (empty content, no progress, progress beyond lines, rounding) covered by unit tests under `tests/`
- [x] 1.3 Create `language_study_anki/web/list.html` (read once at import, fail loudly on missing file like `practice.html`) and verify the Hub renders rows `[{id, title, pcts}]` with four per-skill percentage entries in reading/speaking/listening/writing order and an empty-state message when no `LSA-Article` notes exist
- [x] 1.4 Verify list rows are ordered most-recently-created first and percentages match stored progress fields per the practice-hub spec scenarios (40 lines / ProgReading 10 → 25%)

## 2. Practice page inside the Hub

- [x] 2.1 Extract the practice-page logic from `PracticeDialog` (payload build, bridge dispatch for `lsa:sel:`/`lsa:extract`/`lsa:play:<n>`, TTS play, `markLearnedUpTo` callback) so `HubWindow` composes it, keeping the `web`, `selection`, `mode`, `_lines`, `_translations`, `_article` attributes on the Hub instance for `extract.py` and selftest compatibility; verify the extracted code imports cleanly without Anki
- [x] 2.2 Implement the `lsa:open:<note_id>:<mode>` bridge command that switches the Hub to the practice view for that article (with the existing `ensure_note_suspended` repair and scroll restore), and verify the practice page renders, restores scroll, and marks learned rows exactly as the current dialog does
- [x] 2.3 Add the back control at the left end of the toolbar in `web/practice.html` (before the mode label, visible while scrolling, sends `lsa:back`) and update the template contract comment; verify it renders in all four modes without overlapping the hint at the toolbar's right end
- [x] 2.4 Implement the `lsa:back` bridge command that re-renders the list page from a fresh collection read, and verify percentages reflect an extract made during practice without reopening the Hub
- [x] 2.5 Implement per-page window titles (list page: `Language Study`; practice page: `<mode label> — <title>`) and verify by switching pages both directions
- [x] 2.6 Add bridge state guards so navigation commands are ignored in mismatched page state and selection/extract are ignored outside the practice page, verifying stale callbacks after a page swap log without side effects

## 3. Entry wiring and removal of the old entry

- [x] 3.1 Replace the body of `practice_dialog.open_dialog` with the thin adapter that opens/raises the Hub on the given note+mode practice page, and verify calling it with the same arguments as today (including `parent=None` from selftest) lands on the article's practice view
- [x] 3.2 Register the Tools-menu action `Language Study: Article List` in `__init__.init()` (guarding `mw.col is None`), delete `language_study_anki/browser_menu.py`, and verify the menu opens the Hub, repeated clicks raise the single existing window, and no context-menu items appear in the Browser
- [x] 3.3 Verify the full practice workflow end-to-end in a scratch instance: Tools menu → list → skill entry → practice → extract with `a` (Add dialog prefilled, progress written, counter updates) → back → updated percentage in the list

## 4. Selftest updates

- [x] 4.1 Replace `check_browser_menu` in `selftest_dialog_checks.py` with Hub list-page checks (rows present, percentages, empty state, `lsa:open`/`lsa:back` navigation) and verify the new check passes in the harness
- [x] 4.2 Run the remaining dialog checks (`dialog_modes`, `dialog_restore`, `selection_capture`, `tts`, `extract_all_modes`, `learned_style`) unchanged against the adapter and verify all pass via `tools/scratch-anki.sh`

## 5. Docs and validation

- [x] 5.1 Update `README.md` (entry section: Tools-menu Hub replaces the Browser right-click description; note the single-window navigation) and verify it matches the shipped behavior
- [x] 5.2 Run `openspec validate --change "add-article-list-hub"` and verify it passes with no errors
