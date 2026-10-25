## Why

The `Phone` field of extracted `@EnListen`/`@EnSpeak` notes currently packs
all phonetics onto one space-joined line (e.g. `UK /ɪˈfemərəl/ US /ɪˈfemərəl/`),
which is hard to scan and visually conflates the UK and US pronunciations.
Every other field value in this project already uses `<br>`-separated lines;
`Phone` is the only single-line outlier.

## What Changes

- `format_phonetics()` joins phonetics with `<br>` instead of spaces, yielding
  one phonetic per line: `UK /ɪˈfemərəl/<br>US /ɪˈfemərəl/`.
- Single-region results produce a plain single line (no separator); a failed
  lookup still yields an empty field (behavior unchanged).
- The function's docstring and the covering unit test stop claiming
  "Flutter parity" — the reference app joined with spaces; this is a
  deliberate divergence.
- **Non-goal**: card templates are not touched. Provisioned `@EnListen`/
  `@EnSpeak` templates continue to omit `{{Phone}}`; whether phonetics should
  render on cards is a separate concern.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `practice-extract`: The "Prefilled note content" requirement's `Phone`
  format changes from the single-line `UK /…/ US /…/` to one phonetic per
  line, `<br>`-separated — consistent with the requirement's existing rule
  that all inter-line separators in field values are `<br>` tags.

## Impact

- `language_study_anki/youdao.py` — `format_phonetics()` (join separator +
  docstring)
- `language_study_anki/extract.py` — no code change; consumes the new format
  transparently
- `tests/test_youdao.py` — `test_format_phonetics_flutter_parity` expectation
  and name
- `openspec/specs/practice-extract/spec.md` — two `Phone` format mentions,
  updated via this change's delta spec
