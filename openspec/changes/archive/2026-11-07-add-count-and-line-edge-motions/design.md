## Context

The practice page (`language_study_anki/web/practice.html`) keeps its cursor state (`cur`, `col`, `visual`, `gPending`) at script scope, closed over by a single `keydown` listener registered outside the empty-article guard. All in-line movement funnels through two functions:

- `moveCol(delta)` — clamps `col` to `[0, len]`, then `extendVisual()` + `render()`
- `moveWord(kind)` — computes the target via `nextWordStart`/`wordBack`/`wordEnd`, same tail

`extendVisual()` already re-derives the DOM selection from `visual.anchor` and the current `col`, so any movement that updates `col` while `visual` is active extends the selection automatically. Line-level movement (`goto()`) deliberately cancels the selection (spec: selection confined to one line) and stays that way.

Digits `1`–`9`, `0`, and `$` are unbound on the practice page today (the list page's digit = direct skill pick is a separate document). The `gPending` chord (600 ms timeout, `setTimeout` clearing) is the existing precedent for prefix state. The `?` overlay is static HTML in `#keys`.

See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**

- Count prefix (`3w`, `10l`) for `h`/`l`/`w`/`b`/`e`, working identically for plain cursor movement and for extending an active visual selection.
- `0` = line start, `$` = line end, also in both contexts.
- Visible pending-count badge with ~1 s idle expiry; non-count keys discard the prefix.
- Keymap overlay and self-test coverage for all of the above.

**Non-Goals:**

- Counts on line-level keys (`j`/`k`/`gg`/`G`/`PageUp`/`PageDown`) — decided: they discard the count and keep single-step behavior; `5G`-style line jumps are out of scope.
- Cross-line visual selection (would overturn the single-line selection spec).
- `$` via AltGr layouts (see Risks).
- Any Python/bridge/storage changes; list-page key changes.

## Decisions

### D1: Count state lives at script scope, next to `gPending`

`let countPending = 0` and a timer handle sit beside `gPending`/`caretLive` — outside the `if (D.lines.length > 0)` block — because the `keydown` listener closes over them and `let` inside the block would not be visible to it (the same constraint already documented for `cur`/`col`). The badge element is static toolbar HTML (like `#pf`), present even on an empty article.

*Alternative:* deriving count state from the badge's DOM — rejected: DOM as source of truth for keyboard state is fragile and slower.

### D2: One prefix-intake branch, one discard rule

In the keydown handler, after the overlay guard and the `D.lines.length === 0` guard:

1. `/^[0-9]$/` on `k`: if the key is `0` and `countPending === 0`, fall through to the line-start motion; otherwise `countPending = countPending * 10 + digit`, update the badge, restart the expiry timer, `preventDefault`, return.
2. `h`/`l`/`w`/`b`/`e`: consume `countPending` (default 1), clear badge + timer, run the motion with that count.
3. `0` (no pending count) / `$`: absolute `moveCol` to `0` / `len`, clear any count (there is none by rule 1's fall-through, but `$` may arrive with one), return.
4. **Every other key** (including `j`/`k`/`g`/`G`/PageUp/PageDown/`v`/`Space`/`r`): `clearCount()` before its existing branch runs — one helper call, so no branch can forget it.

This places intake after the overlay guard (digits are inert while `?` help is open, like every other key) and after the empty-article guard (no badge state churn on an empty article).

*Alternative:* a count state machine wrapping the whole handler — rejected: overkill for one prefix and would entangle the `a`/`?`/overlay-open ordering that the current handler carefully documents.

### D3: Counts applied inside `moveCol`/`moveWord`, not by dispatch loops

- `moveCol(delta)` already clamps, so `h`/`l` pass `±count` straight through — no loop needed.
- `moveWord(kind, n)` loops `n` times over the motion primitive **with a stagnation guard**: if a step returns the same `col` it had before (line start for `b`, line end for `w`, last char for `e`), break immediately. `nextWordStart(t, p)` with `p >= t.length` returns `p` unchanged, so without the guard `99w` at line end would spin `n` no-op iterations — harmless but wrong-looking and it defeats the "stop at the line's boundary" spec wording.

Because both functions already end with `extendVisual()` + `render()`, the visual-selection context needs **zero additional code**: `v` + `3w` and `0`/`$` extensions ride the same path. This is the core reason counts are applied here rather than at the dispatch site.

`0`/`$` are implemented as `moveCol(-col)` and `moveCol(len - col)` respectively — absolute targets through the same clamping/extension tail.

### D4: Badge in the toolbar, expiry ~1 s

The badge is a `<span>` in `#toolbar` (styled like `.field`, e.g. `3` in a keycap-ish pill), updated on every digit. Expiry: `clearTimeout` + `setTimeout(clearCount, 1000)` restarted on each digit — a longer window than `gPending`'s 600 ms because typing `10l` involves more pauses, but short enough that a stray digit never causes a surprise jump. `clearCount()` = reset `countPending = 0`, hide badge, clear timer.

*Alternative:* badge next to the caret in the article flow — rejected: it would reflow the line text and complicate `renderCaret()`'s text-node splitting.

### D5: `$` is `Shift+4`; AltGr layouts are documented, not handled

The handler already passes `shiftKey` (it only bails on ctrl/meta/alt), and `?`/`V` prove shifted chars arrive fine in AnkiWebView. On layouts where `$` requires AltGr (Ctrl+Alt), the existing modifier guard drops the key — we accept this: the spec promises `$` as a character key, not a chord. Mitigation is the keymap overlay documenting `0`/`$`, plus `0` still covering line-start.

### D6: Self-test extends `check_keyboard_nav` with a count stage

Reuse the existing synthetic-key pattern (`_keys_js` / `ke()` in `_JS_KBD_PRACTICE`): a new probe sequence fires `3`,`w` (assert `col` advanced by three word steps), `1`,`0`,`l` (assert +10 and badge text), `$`,`0` (assert line-end → line-start), a count + `j` (assert count discarded, single line move), and `v`,`3` (assert selection span). Badge expiry (~1 s) is asserted from Python with a delay between two `runJavaScript` calls, mirroring how other timed behaviors are probed. `col` is read back via script-scope evaluation (the self-test already reads `cur`/cursor state the same way).

## Risks / Trade-offs

- [Stray digit consumed by a non-motion key the user meant as a fresh command] → D2's discard rule: any other key clears the count first, then behaves normally — worst case is the count is lost, never a wrong jump.
- [`99w`-style counts at a boundary could loop or overshoot] → D3 stagnation guard; spec scenario "Count never leaves the line" pins it.
- [`$` unreachable on AltGr layouts] → documented limitation (D5); `0` still works; overlay text shows the key so users can discover availability.
- [Badge adds toolbar width, could crowd the hint on narrow windows] → badge is a few characters, shown only while a count is pending; toolbar already truncates gracefully with `white-space: nowrap` on the hint — verify visually in self-test.
- [Self-test timing: 1 s expiry vs. test flakiness] → probe asserts badge-visible immediately, then uses a Python-side delay > 1 s before asserting expiry; no reliance on sub-second timing.
- [`e` count semantics at word end] → `wordEnd` from the last char of a word advances to the next word's end; with a count this matches repeated `e` presses exactly — no special-casing, but the spec scenario should use `w` (start-of-word, deterministic) as the worked example, which it does.

## Migration Plan

None — pure additive page behavior; no stored data, no schema, no Python changes. Rollback = revert the `practice.html`/self-test edits.

## Open Questions

None — count scope (in-line only), line-level interaction (discard), and badge+expiry presentation were decided with the user before this design.
