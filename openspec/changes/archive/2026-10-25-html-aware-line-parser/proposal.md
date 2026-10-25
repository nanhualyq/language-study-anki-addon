## Why

After an article's `Content` is edited in Anki's rich editor, the practice dialog shows phantom blank lines at the end of the article. Verified against a live note in the user's collection: the editor stores 56 lines as `<div><div>L1</div>…<div>L56</div></div>` (an outer wrapper div around one div per line), and the current regex-based parser — which turns *every* `</div>` into a line break, including the wrapper's closing tag — yields 58 lines with the last two empty. Every line count in the system is therefore wrong: the practice counter (54/58 instead of 54/56), the browser context-menu percentage (93% instead of 96%), and line/translation correspondence in Writing mode. The same class of failure affects markup pasted from web pages (lists, paragraph wrappers, `<style>` blocks, unclosed `<p>`), because the wrapper-vs-line distinction is structural and cannot be resolved by regex substitutions.

## What Changes

- Replace the regex substitution pipeline in `field_to_lines()` with an HTML-aware streaming line extractor built on the Python standard library's `html.parser` (no new dependencies): a **leaf block element yields exactly one line, a container block yields no line of its own, and `<br>` is a hard line break**. The editor's outer wrapper and any pasted container markup stop contributing phantom lines.
- Normalize document edges: leading and trailing empty lines produced by markup are dropped; intentional blank lines *inside* the article are preserved unchanged.
- Harden the parser against markup classes the current code mishandles: whitespace-only data between pasted tags is ignored, CRLF is normalized (`\r` no longer leaks into lines), `script`/`style`/comment content is discarded instead of becoming article lines, and entities are decoded as data so `&lt;br&gt;` can never be mistaken for a separator.
- **BREAKING** (behavior): a field can no longer *end or begin* with a representable blank line — `field_to_lines(lines_to_field(["a", ""]))` returns `["a"]`, not `["a", ""]`. Interior blank lines continue to round-trip. This is the intended fix, but it invalidates one existing round-trip invariant.
- Update the storage test suite: replace the `[:2]` slice assertions (which silently ignored the phantom tail) with exact-equality assertions, and add a scenario matrix covering wrapper divs, `<p>`-wrapped content, empty paragraphs, web-copied lists, unclosed paragraphs, and edge trimming.

No stored data is migrated: existing notes are corrected at read time by the fixed parser. The `field_to_lines()` / `lines_to_field()` signatures and all call sites stay unchanged.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `openspec/specs/article-storage/spec.md`: the **"Line-based content storage"** requirement is redefined. Its current tolerant-parsing rule ("split on `<br>` first, fall back to `\n`") is superseded by a structural rule — HTML block structure determines line boundaries, container wrappers contribute no lines, document-edge empty lines are dropped, and a scenario for rich-editor markup that currently yields phantom trailing lines is added. The write contract (`<br>` as canonical separator) and the empty-content scenario are unchanged.

## Impact

- **Code**: `language_study_anki/storage.py` (`field_to_lines()` rewritten; `lines_to_field()` unchanged).
- **Consumers (behavior improves, no code changes needed)**: `practice_dialog.py` (line rows + `<learned>/<total>` counter), `browser_menu.py` (`_progress_percent`), `extract.py` / `field_builder.py` (context lines, translation-line correspondence, Back resolution), the reviewer card template `{{Content}}` (raw HTML render — unaffected today, unchanged).
- **Tests**: `tests/test_storage.py` (round-trip invariants and wrapper assertions), `language_study_anki/selftest_dialog_checks.py` (line-count expectations use the same parser, so they follow automatically).
- **Risks**: line counts of already-edited notes shrink (that is the fix — stored progress values stay valid because they are clamped); HTML fragments with pathological unclosed nesting rely on small implied-close rules covered by tests; no dependency, no schema, no sync-facing change.
