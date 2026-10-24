## Context

All of this change lives in the `_HTML` template string of `language_study_anki/practice_dialog.py`. The Python side passes a JSON payload `D` (mode, title, lines, translations, progress, progressField) into the template; the web view is `AnkiWebView.setHtml`. Relevant current wiring:

- `#pf` text is set once at load: `D.progressField + ':' + D.progress`.
- The hint is a `.hint` div with `position: fixed; bottom: 8px; right: 14px`, so it overlays the article's bottom-right corner on the last screen.
- `#trans-toggle` (Reading only) bulk-opens/closes every row by driving the same `open` class the per-row twisties use; its listener calls `setOpen` on all rows.
- After a successful extraction, Python calls `window.markLearnedUpTo(line_no)` via `runJavaScript` (`extract.py:187`). It adds the `learned` class to rows and updates `D.progress`, but never touches the toolbar.
- The scroll-restore retry already computes `learnedTo = Math.min(D.progress || 0, D.lines.length)` — the same clamp the counter needs.

## Goals / Non-Goals

**Goals:**
- Toolbar counter shows `<learned>/<total>` and stays truthful immediately after extraction.
- Zero elements overlapping the article body.
- Shortcut key visually distinct in the hint.
- Reading mode uses the same single per-line reveal mechanism as the other modes.

**Non-Goals:**
- No Python-side changes (bridge commands, progress I/O, TTS, extract flow untouched).
- No change to how progress is stored or the `progressField` payload key (it stays in `D` even though the toolbar no longer prints the field name).
- No restyling of lines, twisties, or learned-row opacity.

## Decisions

1. **Counter format `<learned>/<total>`, no field-name prefix.** The mode name already appears left of the counter, so `ProgReading:` was redundant chrome; `12/50` answers "how much is left" directly. Clamp with the same expression as scroll-restore (`Math.min(progress, lines.length)`) so scroll target, learned styling, and counter can never disagree. Empty article renders `0/0` naturally.

2. **Live counter update goes inside `markLearnedUpTo`, not a new bridge message.** `extract.py` already invokes it with the new progress line; extending it to also rewrite `#pf`'s text keeps the single existing callback and avoids touching Python. The function already clamps against `D.lines.length` for row styling, so it reuses the same bound for the counter. Alternative considered: a dedicated `lsa:progress` bridge message — rejected as new protocol surface for two lines of JS.

3. **Hint moves into the toolbar as a right-aligned item (`margin-left: auto`), rendered as `<kbd>` keycap.** The toolbar is already a sticky flex row, so the hint inherits "visible while scrolling" for free and the fixed-position overlay is deleted outright. The `a` becomes a `<kbd>` element with a small border/background treatment (standard semantic element for key names; no new CSS framework). The hint text itself is unchanged.

4. **`#trans-toggle` removal is a four-part cleanup.** Removing only the button would leave dead code: (a) the button markup, (b) the two CSS rules gating its visibility (`#trans-toggle { display: none; }` and `body.mode-reading #trans-toggle { ... }`), (c) its `addEventListener` block, (d) nothing else — `setOpen` stays (twisties use it) and the `open`-class mode rules stay (per-row reveal keys off them). The bulk-toggle state logic (`openAll` computation) goes with the listener.

## Risks / Trade-offs

- [Reading mode loses one-click "reveal all translations"] → Accepted per proposal (user decision). Per-row twisties remain; no single-line behavior changes. Users with large articles must open rows individually.
- [Toolbar gains one more item; narrow windows could crowd] → The removed `#trans-toggle` button (the widest toolbar control in Reading) frees more width than the hint occupies; hint stays at 11px `#aaa`. No other mode had the button, so non-Reading modes gain the hint with an empty slot where the button sat.
- [Counter and row styling could drift out of sync] → Both now derive from the same clamp (`min(progress, total)`) and update in the same `markLearnedUpTo` call, so they change together or not at all.

## Open Questions

None — format, live-update wiring, hint placement/styling, and the toggle removal were all settled in explore mode.
