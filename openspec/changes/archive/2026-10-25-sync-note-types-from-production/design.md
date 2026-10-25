## Context

All note-type construction lives in `language_study_anki/provisioning.py`. Today it builds minimal types: `ARTICLE_FIELDS` (8 fields), `EXTRACT_FIELD_NAMES = [Front, Back, Title, Url, Cover]` with `Phone` appended last for audio types, and bare templates (`{{Front}}` / `{{FrontSide}}<hr>{{Back}}`, no CSS, no browser template, no sticky). The user's production collection — read live via Anki-Connect on 2026-10-25 — holds richer versions of all four types. `ensure_article_notetype` / `ensure_extract_notetype` are resolve-by-name (adopt existing, create when missing) with an additive field-repair loop; they never touch templates or field order of an existing type. See proposal.md for motivation; `specs/article-storage/spec.md` delta for the one spec'd change (Article gains `Cover`).

## Goals / Non-Goals

**Goals:**
- When the addon creates any of the four note types from scratch, the result matches production: field set **and order**, sticky flags, card templates (qfmt/afmt), browser question template, `.card` CSS, and sort field.
- `LSA-Article` gains the `Cover` field (now provisioned, not user-maintained).

**Non-Goals:**
- Reconciling / overwriting templates or field order of note types that already exist in a collection (adopted types are left intact apart from additive field repair).
- Changing `extract.py`, the deck name, the practice dialog, or per-mode field-content behavior.
- Spec'ing card templates (the specs have never described rendering; this change keeps that boundary).

## Decisions

- **D1: Declare each note type's full definition as data and drive `_create_*_model` from it.** A per-name spec (ordered fields with sticky, `qfmt`/`afmt`/`bqfmt`, `css`, `sortf`) replaces the hardcoded minimal construction, so production fidelity is expressed once and stays readable. Alternative considered: keep the bare templates and sync fields only — rejected; the user chose full production parity.
- **D2: `ARTICLE_FIELDS` gains `Cover` (9 fields).** This reverses the prior change's decision to leave `Cover` user-maintained, because production now carries it and the direction is production → code. The article card template/sort field already match production and are unchanged.
- **D3: Match production field order exactly at creation** — non-audio `Front, Back, Url, Title, Cover`; audio `Front, Back, Phone, Url, Title, Cover` (`Phone` third, `Url` before `Title`). `required_extract_fields(name)` returns this ordered list; its **additive-repair** role is unchanged (set-membership check, missing fields appended), so an already-existing partial type is never reordered — only completed. Only freshly created types get the production order.
- **D4: Sticky flags from production** — `Front`, `Back`, `Url`, `Title` sticky; `Phone`/`Cover` not. Applied only at creation (D3's additive repair does not retroactively set sticky).
- **D5: Rich templates + browser template + CSS, verbatim from production.** TTS voice `en_US` is hardcoded to match production. `bqfmt = "{{Front}}"`, `bafmt = ""` for all extract types. Exact strings are the reference block below.
- **D6: Adoption/repair semantics untouched.** `ensure_*` still resolve by name, create only when missing, and add missing fields additively; they never rewrite an existing type's templates, order, sticky, or CSS. The user's production collection is therefore unaffected (all fields present → repair adds nothing).

### Production reference (captured 2026-10-25)

Field order / sticky:
- `LSA-Article`: `Title, Content, Translation, Url, ProgListening, ProgSpeaking, ProgReading, ProgWriting, Cover` — none sticky; `sortf` = Title; qfmt `{{Title}}`; afmt `{{FrontSide}}<hr id="answer">{{Content}}`.
- `LSA-ReadWrite`: `Front*, Back*, Url*, Title*, Cover` (`*`=sticky); `sortf` = Front.
- `LSA-Listen` / `LSA-Speak`: `Front*, Back*, Phone, Url*, Title*, Cover`; `sortf` = Front.

Shared extract CSS: `.card {\n    font-family: arial;\n    font-size: 20px;\n    text-align: center;\n    color: black;\n    background-color: white;\n}\n` (Article adds `line-height: 1.5;`).

Card 1 templates (`\n` = newline):
- header (all three): `<p style="font-size: small; color: gray;">\n{{Deck}} {{#Tags}}#{{Tags}}{{/Tags}}\n{{#Title}} <br>{{Title}} {{/Title}}\n{{#Url}} <br><a href="{{Url}}">{{Url}}</a> {{/Url}}\n</p>\n\n`
- **ReadWrite** qfmt = header + `{{Front}}\n\n{{#Cover}}<br>{{Cover}}{{/Cover}}\n`; afmt = `{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}\n`
- **Listen** qfmt = header + `{{Front}}\n<br>\n{{tts en_US :Back}}\n\n{{#Cover}}<br>{{Cover}}{{/Cover}}\n`; afmt = `{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}\n\n<p>{{Phone}}</p>`
- **Speak** qfmt = header + `{{Front}}\n\n{{#Cover}}<br>{{Cover}}{{/Cover}}\n`; afmt = `{{FrontSide}}\n\n<hr id=answer>\n\n{{tts en_US :Back}}\n\n<p>{{Phone}}</p>`
- all three: bqfmt = `{{Front}}`, bafmt = ``

## Risks / Trade-offs

- [Point-in-time capture drifts if the user edits production again] → Accepted; the sync records the definitions in code, so a future production change requires another sync. The reference block documents the capture date.
- [`{{tts en_US :Back}}` needs Anki's TTS + an `en_US` voice] → Cards degrade gracefully when the voice is absent (TTS field renders empty); extraction/collection behavior is unaffected.
- [Additive repair appends missing fields at the end, not their production position] → Only affects partial foreign types; production is already complete, so its order is untouched. Fresh types use the production order (D3).
- [Self-test decoy plant and provision check assert extract fields via `EXTRACT_FIELD_NAMES`] → Reordered list / added sticky must be reconciled in `selftest_checks.py` (task).
- [Sticky fields retain editor values between adds] → Intentional (matches production); noted so it isn't mistaken for a bug.

## Migration Plan

None. Create-when-missing means the user's production collection is adopted as-is (repair adds nothing). Rollback = revert the provisioning constants/templates. Fresh collections created after rollback return to the minimal types.

## Open Questions

None.
