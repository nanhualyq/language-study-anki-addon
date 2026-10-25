## Why

The addon still provisions the reference app's extract note type names (`@Basic`, `@EnListen`, `@EnSpeak`), which don't follow the `LSA-` prefix convention established when `Article` became `LSA-Article`. Additionally, the user has added a new `Cover` field to their `LSA-Article` notes (e.g. a cover image reference) that should travel with each extraction, exactly like `Title` does today.

## What Changes

- **BREAKING**: Rename the extract note types: `@Basic` → `LSA-ReadWrite`, `@EnListen` → `LSA-Listen`, `@EnSpeak` → `LSA-Speak`. Provisioning creates/adopts/resolves only the new names; the old names are no longer recognized (no migration — established `LSA-Article` precedent: legacy notes stay on the legacy types).
- Add a `Cover` field to all three extract note types (provisioned on creation and added additively to adopted types that lack it).
- During extraction, copy the article's `Cover` value into the extracted note alongside `Title` and `Url`, reading the article defensively (a missing `Cover` field on the article — e.g. on a fresh collection where the field was added manually only on the user's own `LSA-Article` — yields an empty value, never a crash).
- `LSA-Article` itself is unchanged: same name, same provisioned field set, no template changes anywhere.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `openspec/specs/article-storage/spec.md`: The "Auto-provisioning of note types and deck" requirement names the extract target note types (`@Basic`, `@EnListen`, `@EnSpeak` → `LSA-ReadWrite`, `LSA-Listen`, `LSA-Speak`); the adoption scenario names the same types; a new requirement pins the no-migration behavior (legacy-named types are never adopted, renamed, or migrated).
- `openspec/specs/practice-extract/spec.md`: The "Prefilled note content" requirement's per-mode note types change to the new names, and its "All types also carry" clause gains `Cover` copied from the article.

## Impact

- `language_study_anki/provisioning.py`: `EXTRACT_NOTE_TYPES`, `EXTRACT_FIELD_NAMES` (+`Cover`), `AUDIO_EXTRACT_NOTE_TYPES`, `MODE_NOTETYPE`, docstrings.
- `language_study_anki/extract.py`: defensive `Cover` copy into extracted notes; module docstring note-type names.
- `language_study_anki/selftest_checks.py`, `language_study_anki/selftest_dialog_checks.py`: decoy-planting, `prov["extract_notetypes"][...]` keys, and mode expectations use the new names.
- `tests/test_provisioning.py`, `tests/test_browser_menu.py` (and any other tests referencing `@Basic`/`@EnListen`/`@EnSpeak`): names updated.
- `README.md`: note-type names in the extraction table and provisioning description.
- Existing user collections: notes created before this change remain on `@Basic`/`@EnListen`/`@EnSpeak`; new extractions land on the `LSA-*` types (deliberate, per the no-migration decision confirmed with the user).
