## Why

The Hub's article list currently shows only the title and four skill percentages, but every article already carries a user-maintained `Cover` field (raw `<img>` HTML pasted in the editor, e.g. `<img src="paste-....jpg">`). With several articles sharing the same title (e.g. one per episode of a series), the cover image is the only visual cue that distinguishes rows — showing it makes the list scannable.

## What Changes

- Each article row on the Hub list page shows the article's cover as a left-side thumbnail (constrained height, aspect-preserving crop) when `Cover` is non-empty.
- Rows without a `Cover` value keep the current title-plus-skills layout with no placeholder.
- The list-page payload (`list_payload`) gains a per-row `cover` field, read defensively (missing/empty field → empty string).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `practice-hub`: The "Article list page" requirement gains cover-thumbnail display per row and an empty-cover fallback scenario.

## Impact

- `language_study_anki/hub.py` — `list_payload()` adds `cover` to each row.
- `language_study_anki/web/list.html` — row layout becomes cover + content flex; CSS constrains thumbnail size; contract comment updated.
- `tests/test_hub.py` — payload assertions gain `cover` (including the empty/missing-field defensive path).
- No changes to provisioning, extract, card templates, or stored data: `Cover` already exists on the `LSA-Article` note type.
