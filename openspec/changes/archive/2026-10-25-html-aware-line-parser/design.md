## Context

`storage.field_to_lines()` is the single entry point every line count in the addon goes through: the practice dialog's rows and `<learned>/<total>` counter (`practice_dialog.py`), the browser context-menu percentage (`browser_menu.py`), and extraction's context/translation correspondence (`extract.py`, `field_builder.py`). The write side (`lines_to_field()`) already emits canonical `<br>`-joined, escaped text and is unchanged.

The current parser is a substitution pipeline: `<br>` → `\n`, then every `</p>`/`</div>` → `\n`, then open tags deleted, then unescape and split. Each `</div>` produces a break *in addition to* the break its content already produced, and the document-final close always produces one more — so any block-structured field ends with phantom empty lines, and an editor/pasted outer wrapper doubles them. Motivation and live-note evidence are in proposal.md; the behavior contract being replaced is the `article-storage` spec's "Line-based content storage" requirement (delta in `specs/article-storage/spec.md`).

Constraints that shape this design:

- Anki addon runtime: no runtime package installation; stdlib only is strongly preferred (bundling a third-party HTML parser into the addon package would be the only alternative).
- The plain-text line model is already baked in upstream: `build_front()` HTML-escapes each line and adds its own `<mark>`; the practice web view escapes lines again. Rich markup inside a line is never rendered today.
- The round-trip invariant for system-written content, `field_to_lines(lines_to_field(lines)) == lines` (including interior empty lines), must keep holding.

## Goals / Non-Goals

**Goals:**

- One structural rule for "what is a line" that holds for `<br>`-canonical system writes, editor-rewritten block markup, editor/pasted wrapper containers, and web-pasted fragments — with no phantom lines at document edges.
- Correct line totals everywhere at once, achieved by fixing the shared entry point rather than each consumer.
- Zero new dependencies; parser stays a single module-local implementation behind the existing `field_to_lines()` signature.

**Non-Goals:**

- Normalizing or rewriting stored note fields (no write-back on open; no migration task). The fix is read-time only.
- Preserving inline formatting, links, or embedded media as structured content — lines remain plain text (an element with no text yields an empty line; see D6).
- Changing `lines_to_field()` or the canonical write format.
- Changing practice-dialog rendering, selection capture, extraction behavior, or progress semantics.

## Decisions

**D1 — Standard-library streaming parse (`html.parser`) over regex patching or a bundled parser library.**
Alternatives considered:
- *Regex patch* (strip `<br>` before block closes + trim edges): fixes today's note but cannot resolve structure — `<div><div>A</div></div><div>B</div>` still yields a phantom blank line *between* A and B, because regex cannot know which `</div>` closes a wrapper. Rejected as insufficient, not as incorrect.
- *lxml / html5lib*: proper HTML5 tree construction (implied end tags, error recovery) but adds a dependency to an addon that has none; lxml is not pure Python. Rejected for a 50-line parsing problem with a bounded markup vocabulary.
- *`html.parser`*: stdlib, tolerant, event-based, decodes character references itself (`convert_charrefs=True`). Chosen. Its one real gap — no implied end tags for `<p>`/`<li>` — is covered by a minimal rule (D3).

**D2 — Line semantics: leaf block = one line, container block = no line, `<br>` = hard break.**
The extraction is a single pass over parser events with one text buffer and a block stack. Event rules:

| Event | Action |
|---|---|
| block start (`div`, `p`, `li`, `h1`–`h6`, `blockquote`, `pre`, `td`, `th`, `tr`, `table`, `ul`, `ol`, …) | flush buffer **only if non-empty**; push block context |
| data | if buffer is empty and data is whitespace-only (indentation between pasted tags) → ignore; otherwise append (normalizing `\r`) |
| `<br>` | flush **unconditionally** (explicit break — an empty line here is meaningful) |
| block end | if buffer non-empty → flush; else if the block is a leaf **and no line was emitted during its span** → emit one empty line (an empty paragraph *is* a blank line); else → emit nothing (a wrapper's close is not a line; nor is a close after a `<br>` that already ended the line) |
| end of input | flush remaining buffer; drop leading/trailing empty lines |

Worked traces (all covered by tests):

```text
<div><div>L1</div>…<div>L56</div></div>   wrappers: no own line      -> 56 lines, real tail   (the live note)
<div>A</div><div></div><div>B</div>       empty leaf = blank line    -> ['A', '', 'B']        (interior preserved)
<div>A</div><div><br></div><div>B</div>   br-only leaf: one blank   -> ['A', '', 'B']        (interior preserved)
<div>A</div><div></div>                   edge artifact              -> ['A']                 (trailing trim)
<div><div>A</div></div><div>B</div>       wrapper + sibling block    -> ['A', 'B']            (regex fails here)
<ul><li>x</li><li>y</li></ul>             ul container, li leaf      -> ['x', 'y']
<div>A<br>B</div>                         br inside leaf             -> ['A', 'B']
<div>A<br></div>                          br flushed content; leaf exit emits nothing -> ['A'] (no doubled line)
A<br>B<br>                                plain canonical tail       -> ['A', 'B']
```

Container detection is dynamic: a block that started another block while open is a container (its exit never emits an empty line); all other blocks are leaves. The "emit nothing on wrapper exit" branch plus the final edge trim is exactly what removes the phantom lines.

**D3 — Implied close only for `p` and `li`.** On a block start, if the innermost open block is a `p` (or an `li` for a nested `li`), close it first — this is the only unclosed-markup case `html.parser` hands us raw (`<p>a<p>b`). No general error recovery is attempted; a stray unmatched close tag is ignored rather than raising. Rationale: pasted fragments are mostly browser-serialized (well-formed); the two rules cover the common hand-edit cases with ~10 lines.

**D4 — Non-content and boundaries.** `script`/`style` contents and comments are suppressed via a flag/stack in the handler (today their text leaks into lines). Void elements other than `<br>` (`img`, `hr`, `input`, …) produce no events that affect lines. Character references are decoded exactly once by the parser; the parser's output is data, never re-parsed, so `&lt;br&gt;` stays text (keeps `test_escaped_br_text_stays_single_line` passing). `\xa0` is replaced by a space as today.

**D5 — Edge trimming, interior fidelity.** Empty lines are dropped only at the two document edges. This is the recorded **BREAKING** behavior from the proposal: a field may no longer begin or end with a representable blank line, and `field_to_lines(lines_to_field(["a", ""]))` now returns `["a"]`. Rationale: an edge blank line is indistinguishable from exactly the editor artifacts being fixed, and spec explicitly states it. Interior blank lines (the existing round-trip test `["a", "", "b"]`) are untouched.

**D6 — Accepted granularity choices.** Table cells (`td`/`th`) are leaf blocks → one line per cell; `tr`/`table` are containers. An element with no text (`<div><img …></div>`) yields an empty line — no `[image]` placeholder — because the plain-text model discards media everywhere else too (consistent, not a new loss). Recorded as decisions so tests document them; they are edge cases for pasted subtitle-style content.

**D7 — Placement.** The extractor lives inside `storage.py` behind the existing `field_to_lines()` entry point. No new module, no import churn for the five call sites, and the module docstring's "tolerant parser" contract is updated to describe the structural rules.

## Risks / Trade-offs

- [`html.parser` is not an HTML5 tree builder — no implied end tags, no recovery for pathological nesting] → D3's minimal implied-close rules + scenario tests for unclosed markup; worst case is a merged line, never an exception (parser callbacks are total).
- [`convert_charrefs` and buffering quirks in data handling] → rely on defaults; the entity test suite (`&amp;`, `&lt;br&gt;`, `&nbsp;`) is retained unchanged as the guard.
- [Line totals of already-edited notes shrink — e.g. 58 → 56] → this is the fix; stored progress values remain valid because a phantom line can never be extracted (no selectable text), so progress ≤ new total, and both the counter and the percentage already clamp.
- [Edge blank lines become unrepresentable] → recorded as BREAKING in the proposal and asserted in the spec delta; if a legitimate use ever appears, it requires a spec change, not a silent parser tweak.
- [A whitespace-only line collapses to an empty line (and disappears entirely at a document edge)] → covered by the spec delta's "whitespace-only text between elements … normalized away"; no test or real content relies on space-only lines.
- [Exotic pasted markup (tables, deeply mixed inline/block) settles on cell-per-line / block-per-line granularity] → documented in D6 and pinned by tests rather than iterated on ad hoc.

## Migration Plan

Read-time only: ship the addon build; no data migration, no schema change, no sync-visible write. Rollback is a plain code revert — nothing in the collection was touched. First open of each edited article after the update shows corrected totals immediately.

## Open Questions

- Whether to add an opt-in "normalize article" browser-menu action that rewrites a note's `Content`/`Translation` through `lines_to_field()` (explore-round option C) so the stored HTML itself becomes canonical. Deferrable: it neither changes the parser contract, the approach, nor the task breakdown — it would be its own change after this one lands.
