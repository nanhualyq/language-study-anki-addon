## Context

All note-type names live in `language_study_anki/provisioning.py` as constants consumed everywhere else: `EXTRACT_NOTE_TYPES` (`["@Basic", "@EnListen", "@EnSpeak"]`), `MODE_NOTETYPE` (reading/writing → `@Basic`, listening → `@EnListen`, speaking → `@EnSpeak`), `AUDIO_EXTRACT_NOTE_TYPES` (`@EnListen`, `@EnSpeak`), and `EXTRACT_FIELD_NAMES` (`Front`, `Back`, `Title`, `Url`). `ensure_extract_notetype` already provides the spec'd additive field guarantee: adopted foreign types missing a required field get it appended (never renamed/removed). Extraction (`extract.py`, `_open_add_dialog`) builds `field_values` with `("Title", article["Title"])` and `("Url", …)` and writes each pair tolerating a missing target field (`KeyError` → warn). The rename precedent is the archived `rename-article-note-type` change: constants changed, adoption-by-name only, no migration. See proposal.md for motivation and `specs/` for the behavior contract.

## Goals / Non-Goals

**Goals:**
- Provision/adopt/resolve the extract types exclusively as `LSA-ReadWrite`, `LSA-Listen`, `LSA-Speak`.
- Guarantee a `Cover` field on all three extract types (creation + additive repair of adopted types).
- Carry the article's `Cover` value into every extracted note, like `Title`/`Url`, with an empty fallback when the article has no value.

**Non-Goals:**
- Migrating, renaming, or adopting legacy `@Basic`/`@EnListen`/`@EnSpeak` types or their notes.
- Provisioning `Cover` on `LSA-Article` (the user maintains that field manually on their own collection).
- Rendering `Cover` in any card template (store-only, per user decision).
- Changing `LSA-Article`'s schema, the `English` deck name, or the practice-dialog/browser-menu behavior.

## Decisions

- **D1: Change the constant values; drop the old names entirely.** `EXTRACT_NOTE_TYPES` becomes `["LSA-ReadWrite", "LSA-Listen", "LSA-Speak"]`, `MODE_NOTETYPE` maps reading/writing → `LSA-ReadWrite`, listening → `LSA-Listen`, speaking → `LSA-Speak`, `AUDIO_EXTRACT_NOTE_TYPES` becomes `("LSA-Listen", "LSA-Speak")`. Every consumer imports the constants, so no call sites need restructuring. Alternative considered: a legacy-name alias/mapping layer — rejected as indirection with no benefit; nothing outside legacy collections depends on the old names (same rationale as `rename-article-note-type` design).
- **D2: No migration, no in-place rename (user decision).** On first extraction in an old collection the confirmation lists the missing `LSA-*` types and creates them alongside the legacy ones; legacy notes stay attached to legacy types. Alternative considered: renaming existing types in place via the model manager (notes follow automatically) — rejected: the user chose the `LSA-Article` precedent, and `@Basic` in particular is a shared/reference name that might be used by other add-ons, making a forced rename surprising.
- **D3: `Cover` on the extract types is addon-provisioned; on `LSA-Article` it is user-maintained (user decision).** Adding `"Cover"` to `EXTRACT_FIELD_NAMES` gets both behaviors for free: newly created extract types include it, and the existing additive-repair loop in `ensure_extract_notetype` appends it to adopted types that lack it. `ARTICLE_FIELDS` stays unchanged. Extraction reads the source defensively (`article.get("Cover", "")`-style), so an article without the field — e.g. on a fresh collection — yields an empty `Cover`, never a crash. Consequence (accepted): extractions from freshly provisioned collections always carry an empty `Cover` until the user adds the field to their `LSA-Article` type.
- **D4: Copy at the single existing copy point, no template edits.** Extend the `field_values` list in `_open_add_dialog` with `("Cover", <article value>)`; the existing per-field `KeyError` tolerance remains the belt-and-braces layer for adopted types. The `qfmt`/`afmt` templates of every type stay untouched (Cover is stored, not rendered).

## Risks / Trade-offs

- [Split study history: pre-change notes stay on legacy types without `Cover`] → Accepted per D2; the user can consolidate later via Anki's built-in "Change Note Type" or a manual rename in the GUI. The new requirement "Legacy extract note types are never adopted" makes this behavior explicit.
- [Fresh collections always extract an empty `Cover`] → Accepted per D3; documented in the delta scenario "Article without a Cover value". Adding `Cover` to `LSA-Article` later is additive and picked up immediately by the defensive copy.
- [Leftover old-name references break self-tests or docs] → Mitigated by a grep task over `language_study_anki`, `tests`, `tools`, and `README.md` for `@Basic`/`@EnListen`/`@EnSpeak` before completion.
- [Selftest decoy currently plants a legacy-named type] → The adoption/repair selftest check plants its decoy under an `LSA-*` name instead, keeping the additive-repair evidence path intact.

## Migration Plan

None. Ship the renamed addon: on first extraction the `LSA-*` types are offered alongside any legacy types. Rollback = revert the constant values, with the same no-migration caveat in reverse.

## Open Questions

None.
