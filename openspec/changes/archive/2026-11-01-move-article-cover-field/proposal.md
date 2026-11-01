## Why

The `Cover` field on `LSA-Article` is the last field of the note type, so it sits at the very bottom of the editor — far from `Title`, where a user actually sets an article's cover image. Moving it to the second position (right under `Title`) makes the editing flow match how the field is used.

## What Changes

- Reorder `ARTICLE_FIELDS` in `provisioning.py`: `Cover` moves from last to index 1 → `Title, Cover, Content, Translation, Url, ProgListening, ProgSpeaking, ProgReading, ProgWriting`. New note types are created in this order.
- Update the comment above `ARTICLE_FIELDS` ("production is the source of truth … matches it exactly"): existing collections are aligned **manually** by the user via Anki's Fields dialog — Anki's backend remaps existing notes' stored values on reposition, so no addon-side migration is performed (explicit non-goal).
- Update the `test_article_parity` expectation in `tests/test_provisioning.py` to the new order.
- Remove the stale docstring in `selftest_dialog_checks.py` (`_ensure_article_cover_field`) claiming the addon does NOT provision `Cover` on articles — it contradicts `provisioning.py`, where `Cover` is part of `ARTICLE_FIELDS`.

Non-goals:

- No addon-side migration/reorder of existing collections (user does it once, manually).
- No change to the three extract note types (`LSA-ReadWrite`/`LSA-Listen`/`LSA-Speak`) or their `Cover` position.
- No runtime code changes: every field read/write in the addon is by field name (`note["Cover"]` etc.), so field order affects only the editor display, provisioning, and tests.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `article-storage`: the "Article note type" requirement states the field order — `Cover` becomes the second field instead of the last.

## Impact

- `language_study_anki/provisioning.py` — `ARTICLE_FIELDS` order + comment
- `tests/test_provisioning.py` — `test_article_parity`
- `language_study_anki/selftest_dialog_checks.py` — stale docstring only (behavior unchanged)
- `openspec/specs/article-storage/spec.md` — via delta (field order in the "Article note type" requirement)
- No API, dependency, or data-format changes; `sortf` stays 0 (`Title` remains the sort field)
