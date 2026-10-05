## Context

All note-type and deck names are centralized in `language_study_anki/provisioning.py`: `ARTICLE_NOTE_TYPE = "Article"` is imported by `browser_menu.py`, `practice_dialog.py`, `suspension.py`, and the selftests. Provisioning adopts an existing note type by exact name, which is why a generic name like `Article` risks colliding with a same-named type from another source. Motivation is in proposal.md; requirements are in the delta specs.

## Goals / Non-Goals

**Goals:**
- Provision and recognize the article note type exclusively as `LSA-Article`.
- Keep the rename a single-constant change; no behavioral change beyond the name.

**Non-Goals:**
- No migration of existing notes or collections (production use has not started).
- No rename of the article deck (`Articles`) or the extract target note types (`@Basic`, `@EnListen`, `@EnSpeak`).
- No change to note type fields, templates, or sort field.

## Decisions

1. **Change the value of the existing `ARTICLE_NOTE_TYPE` constant to `"LSA-Article"` rather than introducing a mapping or alias layer.** Every consumer already imports the constant, so one edit propagates everywhere. Alternative considered: keep `"Article"` and map to the new name at the Anki boundary — rejected as indirection with no benefit since nothing depends on the old name.
2. **Name the type `LSA-Article` per the chosen `LSA-` prefix.** Alternative considered: an `@`-style prefix (`@Article`) to match the extract target types — rejected: the user chose `LSA-`, and the `@` group already denotes extract targets, so reusing it would blur that distinction.
3. **Leave the internal template name ("Article card") unchanged.** Template names are scoped inside their own note type and cannot collide with anything external; renaming them adds churn without observable benefit.

## Risks / Trade-offs

- [Dev collections created before the rename still contain an `Article` note type with addon notes] → Accepted: production has not started; the stale type and its notes are simply ignored and can be deleted manually in a dev collection.
- [`LSA-Article` itself could collide if the prefix is reused elsewhere] → Mitigated by the user-specific prefix; adoption-by-name behavior is unchanged and intentional.

## Migration Plan

None. Ship the renamed addon; on first use provisioning creates `LSA-Article` alongside (not instead of) any legacy `Article` type. Rollback = revert the constant value, with the same no-migration caveat in reverse.

## Open Questions

None.
