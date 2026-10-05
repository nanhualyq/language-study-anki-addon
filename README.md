# language-study-anki-addon

A native Anki addon that runs the four-skill English study workflow (listening /
speaking / reading / writing) **inside Anki**. Articles live as notes in the
collection — no AnkiConnect, no sidecar app.

Ported from the reference implementation `../my_english_ankier_flutter`; see
`openspec/` for the full change history, specs, and design decisions.

## Features

- **Articles as notes** — `Article` note type (Title / Content / Translation /
  Url + four progress fields), dedicated deck, cards auto-suspended so articles
  never enter the review queue. Note types and decks are auto-provisioned on
  first use and adopted by name when they already exist.
- **Browser-native entry** — right-click an `Article` note →
  `Practice: Listening / Speaking / Reading / Writing`.
- **One practice dialog, four modes** — line-based rendering, scroll restore to
  the last extracted line, learned-line styling that updates live after an
  extract, per-line TTS (listening/speaking only).
- **Extract with `Ctrl+E`** — builds a prefilled note in Anki's native Add
  dialog (deck `English`), per the reference behavior:

  | Mode | Note type | Front | Back | Phone |
  |---|---|---|---|---|
  | Reading | `@Basic` | source + `<mark>` | Youdao definition (fallback: translation line) | — |
  | Writing | `@Basic` | **translation** + `<mark>` | source line at same index | — |
  | Listening | `@EnListen` | source, selection masked as `???` | selected text | phonetics |
  | Speaking | `@EnSpeak` | source + `<mark>` | selected text | phonetics |

- **Progress = extract-only** — four separate fields, monotonic, written only
  when an extract opens the Add dialog (never on scroll or dialog close).
- **TTS** — reuses Anki's built-in engine (`aqt.tts` / SAPI on Windows) with
  content-hash caching and interrupt-on-new-playback.

## Requirements

- Anki 26.8.1 or later (developed and verified against 26.8.1).

## Install

Copy (or symlink) the `language_study_anki/` directory into your Anki add-on
folder and restart Anki:

```
%APPDATA%\Anki2\addons21\language_study_anki
```

Or run the deploy script, which copies the add-on into the default base,
backs up any previous install, and carries over its `meta.json`:

```
tools/deploy-prod.sh          # add --dry-run to preview, --force if Anki is running
```

No configuration needed — everything is provisioned on first use.

## Development

### Run a scratch instance (never touches your real collection)

```bash
# isolated base inside the repo (.scratch-anki/, gitignored)
tools/scratch-anki.sh            # leaves Anki running; close its window when done
tools/scratch-anki.sh --fresh     # wipe the base first (re-create the profile, see below)
```

If you use `--fresh`, re-create the `dev` profile headlessly (needs Anki's
bundled Python, available as `~/anki-bin/python/bin/python3` inside WSL):

```bash
python tools/create_profile.py <repo>/.scratch-anki dev
```

Note: launch Anki with `ANKI_SINGLE_INSTANCE_KEY` set (the script does this) —
otherwise a running production Anki swallows the launch with
"Already running; reusing existing instance."

### Self-test suite (10 checks, runs inside the addon)

```bash
LSA_SELFTEST=1 LSA_SELFTEST_KEEP=1 tools/scratch-anki.sh
# results → .scratch-anki/selftest-results.json (each check: {"ok": bool, "detail": ...})
```

Covers provisioning/adoption, card suspension, Add-dialog `set_note`,
database hygiene, browser menu labels, mode rendering, scroll restore,
selection capture, TTS, and four-mode extraction (note types, field kinds,
progress writes). `LSA_SELFTEST_KEEP=1` keeps Anki open afterwards for a
manual pass.

### Unit tests (zero dependencies)

```bash
python -m unittest discover -s tests -t .
```

53 tests cover line storage round-trips, progress monotonicity, Front/Back
construction, and the Youdao client (entries + phonetics, all failure paths).

## Repository layout

```
language_study_anki/   addon package (entry: __init__.py)
tests/                 unit tests (stdlib unittest)
tools/                 dev launchers & helpers
openspec/              specs, design, and change history
```
