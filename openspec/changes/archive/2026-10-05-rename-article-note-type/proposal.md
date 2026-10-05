# Proposal: rename-article-note-type

## Why

The addon provisions an Anki note type named `Article`, which is too generic: the provisioning logic adopts existing note types by exact name, so any collection that already has a note type named `Article` (from another addon or manual creation) would be wrongly adopted instead of the addon's own definition. A distinctive personal prefix avoids the collision.

## What Changes

- Rename the addon-provisioned article note type from `Article` to `LSA-Article`.
- Update provisioning, browser context-menu gating, practice-dialog note checks, and selftests to use the new name (all code reads a single `ARTICLE_NOTE_TYPE` constant).
- **BREAKING**: existing collections already containing an `Article` note type created by the addon will not be migrated — no migration is required because production use has not started.

## Capabilities

### New Capabilities

_None_

### Modified Capabilities

- `openspec/specs/article-storage/spec.md`: The "Article note type" requirement and the "Auto-provisioning of note types and deck" requirement name the provisioned note type; both change from `Article` to `LSA-Article`.
- `openspec/specs/practice-dialog/spec.md`: The "Browser context-menu entry" requirement's scenarios distinguish article notes by note-type name; both change from `Article` to `LSA-Article`.

## Impact

- Code: `language_study_anki/provisioning.py` (`ARTICLE_NOTE_TYPE` constant and template naming), consumed by `browser_menu.py`, `practice_dialog.py`, `suspension.py`, and selftests (`selftest_checks.py`, `selftest_dialog_checks.py`) via the constant.
- Specs: delta updates in `article-storage` and `practice-dialog`.
- Data: no migration of existing notes or decks; the article deck name (`Articles`) and extract target note types (`@Basic`, `@EnListen`, `@EnSpeak`) are unchanged.
