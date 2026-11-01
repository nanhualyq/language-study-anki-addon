# Design — add-vim-keyboard-navigation

See proposal.md for motivation. The requirements (what the user observes) live in the two delta specs: `specs/practice-hub/spec.md` and `specs/practice-dialog/spec.md`.

## Context

Both Hub pages are HTML rendered in one `AnkiWebView` per window (`hub.py` swaps pages via `setHtml`). Every user-visible action already crosses the JS→Python bridge as an `lsa:*` command (`hub.py::_on_bridge`), and the extract pipeline consumes a plain JSON dict `dialog.selection = {line, start, end, text}` produced client-side by `computeSel()` from the DOM selection and sent via `lsa:sel:`. The only existing keyboard handler is the bare-`a` extract shortcut in `practice.html`. The self-test (`selftest_dialog_checks.py`, `selftest_checks.py`) probes the DOM through stable selectors (`.row`, `.row .skill`, `.title`, `.pct`, `.name`, `[data-line]`, `[data-twisty]`, `.sel-area`, `#toolbar` first child `#back`).

Constraints discovered during exploration:

- `AnkiWebView` may intercept modifier-based shortcuts (Ctrl+F etc.); plain keys demonstrably reach the page (the existing `a` handler works). The design therefore uses no Ctrl/Meta/Alt combinations.
- The extract contract is single-line (`{line, start, end, text}` with one line index); multi-line selection has no consumer.
- In Listening mode the `.primary` text is `display:none` until the line is opened, so no selection or caret can exist on a closed line there.

## Goals / Non-Goals

**Goals:**

- Remove the mouse from the study loop (list → practice → reveal/play → extract → back) with vim-style keys at "medium" depth: two-level cursor, word motions, v/V visual selection.
- Zero Python-side change: every action reuses an existing bridge command and the existing selection→extract pipeline.
- Additive DOM/CSS so all existing self-test probes keep passing unchanged.

**Non-Goals:**

- Multi-line visual selection and multi-line extract (would change the Python extract contract).
- Full-vim machinery: count prefixes (`5j`), `f`/`t` character search, text objects (`iw`, `ap`), marks, macros, `/` search/filter on the list page.
- Ctrl-based scrolling (`C-d`/`C-u`/`C-f`/`C-b`) — unreliable in AnkiWebView.
- Changing any existing mouse behavior.

## Decisions

**D1 — The keyboard layer lives entirely in `web/list.html` and `web/practice.html`.**
Each page gains a self-contained JS module (keydown handler + cursor state + render helpers) and CSS. Rationale: every action is already a bridge command; putting the layer in Qt would duplicate state across the bridge for no gain. Alternative (Qt `QShortcut`s forwarding commands) rejected: it splits the interaction model in two and can't do in-line carets or visual selection.

**D2 — Visual selection = programmatic DOM selection.**
`v`/`V` (and their extension moves) call `Selection.setBaseAndExtent()` on the focused line's `.primary` text node. The browser then fires `selectionchange`, the existing listener runs `computeSel()`, and `lsa:sel:` carries the dict to Python exactly as a mouse selection would. `a` therefore needs no change at all, and highlight/trim/single-line rules come free. Alternatives considered: (a) synthesizing the `{line,start,end,text}` dict in JS and bypassing the DOM — rejected because it forks the selection pipeline (two producers, divergence risk in trimming logic) and renders no highlight; (b) a custom highlight layer (Range + `getClientRects` painted with absolutely-positioned divs) — rejected as far more code for the same result.

**D3 — Plain keys only.**
All bindings are letters, digits, `Enter`, `Esc`, `Space`, `?` (shift+/). No Ctrl/Meta/Alt combos anywhere. Rationale: AnkiWebView's interception of modifier shortcuts is version-dependent and untestable from JS. `gg` is implemented as a pending-`g` state with a ~600 ms timeout inside the page, not as a chord requiring Qt.

**D4 — Cursor rendering is purely additive, and never touches the row background.**
List page: `.krow` / `.kskill` classes reusing the existing hover-look for the focused skill. Practice page: `.kcursor` class on the focused `.line` draws a left accent bar via an inset `box-shadow` (which paints inside the row independently of its background) plus a `<span class="caret">` wrapping one character inside `.primary`. Critically, `.kcursor` sets **no `background`** — the learned dark band (`.line.learned { background: #333 }`) and the row's own tint are left exactly as-is, so the cursor composes with either. This was corrected during apply: the first cut gave `.kcursor` its own background (a tint / transparent reset), which broke the dark-row self-test (`learned_style`) because its probe reads the *computed background* of the first `.line.learned` — also the initial cursor line in Listening mode — and no longer saw `#333`. The accent-bar-only design keeps the band intact at every cursor position. No existing element is restructured, renamed, or reordered, so every self-test selector keeps matching. The toolbar hint text changes to advertise `v`/`a` and `?`.

**D4a — Caret is deferred on load so the mouse-probe text node stays pristine.**
The caret is gated behind a `caretLive` flag that starts `false` and flips `true` only on first keyboard use; `renderCaret()` returns early until then. Without this, the caret span would wrap the first character on load and the existing mouse-driven self-test probes (which build a `Range` from `.sel-area`'s `firstChild` and assume pristine text) would misread the selection. The caret renders as a bar-only span (no background — see the risk table).

**D5 — One cursor state object per page, rendered centrally.**
Practice: `{cur, col, visual: {anchorCol} | null}`; render on every state change (line class, caret span, selection). List: `{row, skill, menu: {index} | null}`; when `menu` is non-null, `j`/`k`/`Enter`/`Esc` are routed to the menu and the row/skill cursors are inert. Rationale: single render path avoids stale-highlight bugs; the menu sub-state is a three-key modal and doesn't warrant a general keymap engine.

**D6 — Caret rendering defers to any active selection.**
While a DOM selection exists (mouse-made or visual), the caret span is not rendered and caret moves (`h`/`l`/`w`/`b`/`e`) instead move the selection. A mouse drag-select also syncs `cur`/`col` to the selection's line/offset via `selectionchange`, so `j` continues from where the mouse left off. Rationale: the caret span rewrites the `.primary` text node, which would destroy an in-flight selection.

**D7 — Word definition.**
Words are runs of `[A-Za-z0-9_]` plus runs of CJK code points (`一-鿿`), with every other non-space character a single-char word. Rationale: the primary content is English (source lines) and Chinese (translations in Writing mode); this matches the double-click word behavior closely enough for `w`/`b`/`e` and keeps the rule one regex.

**D8 — Listening mode auto-reveals for `v`/`V`.**
`v`/`V` on a closed Listening line first toggles the line open (same code path as `Enter`), then selects. `p`/`Space` play without revealing. Rationale: the primary text is `display:none` there; playing hidden text is the mode's normal use, selecting it is not possible.

**D9 — Key roles.**
Practice: `j/k/gg/G` line, `h/l/w/b/e` char, `v` charwise visual starting collapsed on the CURSOR character (vim parity — no automatic word selection; word picks come from `v`+`e`/`w` motions), with a second `v` cancelling, `V` visual line-select, `a` extract (consumes the selection — see D12), `Enter` reveal toggle, `p`/`Space` TTS, `q` back, `?` overlay. List: `j/k` row, `h/l` skill (wrapping), `1-4` skill direct, `Enter`/`o` open, `A` add, `m`/`.` menu toggle (second press closes — keyboard- or mouse-opened), `?` overlay. `Escape` is bound NOWHERE (see D11); cancellation and closing are toggle presses of the key that opened the thing.

**D10 — Keymap overlay is a page-local fixed-position element** listing the bindings, toggled by `?` (pressed twice to dismiss), and it never touches page state. No Python involvement.

**D11 — Escape is deliberately UNBOUND (supersedes the earlier consume-Escape approach).**
AnkiWebView injects its own page-level listener on every page load (`AnkiWebView._on_load_finished`): `keydown → evt.key === "Escape" → pycmd("close")`. Anki's internal bridge dispatch routes `close` to `AnkiWebView.onEsc`, which closes the parent window — the Hub is a QMainWindow, so Escape closes it. The injected listener is registered AFTER the page's own scripts, and `preventDefault()` does not stop other listeners on the same node, so no amount of page-side handling can block it (verified against the deployed 26.9.3 build; the earlier "consume Escape in every state" could not work). Consequences: the keymap uses no Escape binding at all — cancel visual selection = second `v`, close row menu = second `m`/`.`, close overlay = second `?` — and a static test guards that neither template ever binds `k === 'Escape'`. Users pressing Escape get Anki's standard tool-window close behavior. A JS `stopImmediatePropagation()` could technically outrun the later-registered injected listener, but that relies on Anki's injection order and is deliberately not used.

**D12 — `a` consumes the selection (user review).**
After `a` fires the extract, the page cancels the active selection (visual or mouse-made). Rationale: the selection has served its purpose; a lingering highlight invited a stray second `a`, double-extracting the same span, and the post-extract state is now uniformly predictable — every action resolves the state it touched (j/k/G/gg cancel visual, second `v` cancels, `a` consumes). Ordering matters: `pycmd('lsa:extract')` is sent BEFORE the clear, because Python captures the selection synchronously in `run_extract` and the bridge delivers messages in order — the `lsa:sel:null` that follows cannot race the extract. Verified: `extract.py` threads the captured `sel` dict through the whole async lookup chain and never re-reads `dialog.selection`.

## Risks / Trade-offs

- [`Esc` may be intercepted by AnkiWebView on some versions] → `q` provides the same return-to-list path, and the apply phase verifies `Esc` reaches the page in the self-test harness (dispatch a synthetic `KeyboardEvent` and check state); if `Esc` is genuinely swallowed, cancel-selection stays mouse+`v`-toggle and the spec scenario for `Esc` is revisited.
- [`gg` pending state could swallow a lone `g`] → the pending window is short (~600 ms) and no other binding starts with `g`; a lone `g` is a no-op, matching vim.
- [Caret re-render vs. mouse selection] → D6's deferral rule; also the caret is never rendered inside `.learned` rows at a position that would require re-escaping (lines are stored as plain text and re-inserted with `textContent`, so no HTML injection surface is added).
- [Native `::selection` highlight on dark `.learned` rows may be low-contrast] → the practice CSS adds a page-scoped `::selection` color that works on both light and dark rows; verified visually in the apply phase.
- [Self-test breakage] → the change is additive-only in the DOM; the existing self-test suites are run unchanged as the acceptance gate, plus new keyboard-flow checks that dispatch synthetic key events.
- [Cursor line vs. learned-row computed background] → CAUGHT and FIXED in apply: the first `.kcursor` styling set its own `background`, which overrode `.line.learned { background: #333 }` on the initial cursor line (line 1 is both learned and the cursor line in Listening mode), so `learned_style`'s computed-background probe read the cursor's tint instead of `#333` and failed `== DARK`. Resolution is now the D4 rule (`.kcursor` sets no background — accent bar + caret only). The in-Anki suite is the acceptance gate that surfaced this; all 16 checks pass after the fix.
- [Caret mistaken for a selection] → the caret is a thin blinking bar (box-shadow on a wrapped-char span, NO background), so it cannot be confused with the filled `::selection` band (user report: the first cut gave the caret char a 28 %-blue background that read as a one-character selection); a measurement-failure degrade is unnecessary because the span wraps the character itself.
- [Escape closes the Hub window] → ROOT-CAUSED and RESOLVED by removal (D11): Anki injects `Escape → pycmd("close") → AnkiWebView.onEsc` into every page after its own scripts; page-side preventDefault cannot block a separate listener. The keymap now binds no Escape — toggles (`v`/`m`/`?`) cover every cancellation — and a static test forbids re-adding an Escape binding. Round-1's "consume Escape in every state" was superseded and could never have worked.
- [`v` selecting an entire Chinese line] → ROOT-CAUSED and FIXED (D7): CJK runs counted as one word, so `v` on a translation selected the whole line; every CJK character is now its own word. Also fixed in the same pass: visual extension used the inclusive cursor offset as an exclusive range end, dropping the cursor character from `e`/`b`/`h`/`l` extensions (off-by-one); jsdom-verified per-character CJK selection, inclusive extension, and second-`v` cancellation.

## Migration Plan

None: no data, schema, or bridge-contract changes; the add-on is redeployed by the existing copy/symlink flow and rollback is restoring the previous files. The updated template contract comments keep the `lsa:*` command list unchanged (keyboard layer is documented as a comment addition).

## Open Questions

- Overlay contents/ordering and exact scroll margin (lines of context kept above/below the cursor) are visual polish; they can be tuned during implementation without changing the specs, the approach, or the task breakdown.
