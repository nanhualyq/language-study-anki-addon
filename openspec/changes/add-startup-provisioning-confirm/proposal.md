## Why

Note types are currently provisioned lazily with no user involvement: on a
clean collection nothing exists until the first extract silently creates
`LSA-Article`, `@Basic`, `@EnListen`, `@EnSpeak`, and the decks. A user who
wants to create an `LSA-Article` note by hand has to read the source to learn
the eight field names. Provisioning should happen automatically during
initialization — and because it mutates the collection, only after the user
confirms. The extract target types are only needed when extracting, so they
stay lazy but become confirmed at extraction time.

## What Changes

- **Startup stage**: on profile open, if the `LSA-Article` note type is
  missing, show a **single confirmation dialog listing exactly the missing
  items** and create it on acceptance (adopt-by-name and idempotence as
  today). If it already exists, no dialog appears.
- **Extract stage**: the extract target note types (`@Basic`, `@EnListen`,
  `@EnSpeak`) and deck `English` remain lazy but become **confirmed** — the
  first extraction shows the same kind of listing dialog before creating
  anything; declining cancels the extraction (no Add dialog, no note).
- **Decline semantics**: nothing is persisted; the startup confirmation is
  re-offered at the next profile open, the extract confirmation at the next
  extraction — until accepted.
- **The `Articles` deck is dropped entirely**: it is a plain deck with zero
  runtime consumers (article cards stay out of review via suspension alone),
  so provisioning no longer creates it and no code checks article deck
  residence. Spec and README are updated accordingly.
- Under `LSA_SELFTEST` no confirmation dialog is shown (auto-accept), so the
  headless self-test harness is never blocked by a modal.
- README updated: the "provisioned on first use" claim is replaced by the
  two-stage, confirmed behavior; the dedicated-deck claim is removed.

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `article-storage`: The **Auto-provisioning of note types and deck**
  requirement becomes two-stage and confirmation-gated (article type at
  profile open, extract targets at extraction) and stops provisioning an
  article deck; **Articles never enter the review queue** drops the
  dedicated-article-deck clause (suspension alone is the mechanism).
- `practice-extract`: The **Keyboard shortcut triggers extraction**
  requirement gains a precondition scenario — extracting while extract
  targets are missing asks for confirmation, and declining cancels the
  extraction (no Add dialog, no note).

## Impact

- `language_study_anki/__init__.py` — register the new startup hook alongside
  the existing registrations.
- `language_study_anki/provisioning.py` — scoped `missing_items(col, scope)`
  helper; article/extract provisioning entries split by scope; **remove
  `ARTICLE_DECK`, its creation, and the `article_deck_id` return key**;
  stays aqt-free (unit-test contract).
- New `language_study_anki/provisioning_ui.py` — shared confirm-and-provision
  helper (lazy aqt imports) + `profile_did_open` registration.
- `language_study_anki/extract.py` — confirm with `scope="extract"` before
  creating anything; abort the extraction when declined.
- `language_study_anki/selftest_checks.py`, `selftest_dialog_checks.py` —
  five references to `ARTICLE_DECK`/`article_deck_id` retargeted to an
  existing deck.
- `tests/` — unit tests for scoped `missing_items` and the dialog
  message builder.
- `README.md` — provisioning wording; dedicated-deck claim removed.
- Design decision D7 ("provisions lazily on first use … not at addon load",
  including the article deck) is superseded; recorded in this change's
  `design.md`.
