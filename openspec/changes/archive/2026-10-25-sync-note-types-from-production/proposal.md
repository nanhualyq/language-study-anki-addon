## Why

The user's production Anki collection holds the latest, most complete versions of the addon's note types (all four were edited today), but the addon's provisioning definitions in `provisioning.py` lag behind. As a result any fresh collection — a new device, a re-created profile, or the self-test base — gets bare, incomplete note types that don't match what the user actually studies with. The production collection is the source of truth; the code should be synced to it.

## What Changes

- **LSA-Article gains a `Cover` field**: `ARTICLE_FIELDS` grows from 8 to 9 (adds `Cover` at the end), matching production. This reverses the earlier decision to leave `Cover` user-maintained — the addon now provisions it.
- **Extract note types (`LSA-ReadWrite`/`LSA-Listen`/`LSA-Speak`) synced to production**:
  - **Field order** matches production: non-audio `Front, Back, Url, Title, Cover`; audio `Front, Back, Phone, Url, Title, Cover` (note `Phone` sits 3rd and `Url` precedes `Title` — the code currently builds `Front, Back, Title, Url, Cover, [Phone]`).
  - **Sticky fields**: `Front`, `Back`, `Url`, `Title` marked sticky (as in production); `Phone`/`Cover` not sticky.
  - **Rich card templates** replace the bare `{{Front}}`/`{{FrontSide}}<hr>{{Back}}`: a gray metadata header (`{{Deck}}`, `#{{Tags}}`, `Title`, linked `Url`), then `{{Front}}`, TTS of `Back` on the Listen question / Speak answer, a conditional `{{#Cover}}…{{/Cover}}` block, and `{{Phone}}` on audio answers.
  - **Browser question template** `{{Front}}` (new — the code sets none).
  - **Explicit `.card` CSS** and `sortField: Front` (currently left to Anki defaults).
- **Provisioning behavior unchanged in spirit**: still create-when-missing plus additive field repair. Existing note types are adopted by name and, if a field is missing, that field is added — but templates and field order of an already-existing type are **never** overwritten.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `openspec/specs/article-storage/spec.md`: The "Article note type" requirement's field list gains `Cover` (now `Title, Content, Translation, Url, ProgListening, ProgSpeaking, ProgReading, ProgWriting, Cover`), with `Cover` noted as MAY be empty.

## Impact

- `language_study_anki/provisioning.py`: `ARTICLE_FIELDS` (+`Cover`); extract field order + sticky flags; new per-type template/CSS/browser/sort-field constants; `_create_article_model` and `_create_extract_model` produce production-identical types; `required_extract_fields` reflects the production field order (its additive-repair role is unchanged).
- `language_study_anki/selftest_checks.py`: the decoy-plant / provision-adoption check may need its expected extract field list/order adjusted if it asserts exact ordering (it currently uses `EXTRACT_FIELD_NAMES`, which is reordered).
- No change to `extract.py` (it already writes `Cover`/`Phone`/`Title`/`Url` into extract notes by name), and no change to `practice-extract` specs — the per-mode field-content requirements are untouched; card templates were never spec'd.
- Fresh collections (and the self-test base) now receive production-identical note types. The user's existing production collection is unaffected (adopted by name; all fields already present, so repair adds nothing and templates are left alone).
