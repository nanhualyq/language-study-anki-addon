## Why

The language-study workflow (four-skill English practice over articles, with vocabulary extraction into Anki) currently lives in two standalone apps — `my_english_ankier_flutter` and `my-english-ankier` — that both talk to Anki over AnkiConnect HTTP as an external sidecar. This repository packages the workflow as a native Anki addon, so articles live *inside* the collection as notes, the AnkiConnect bridge disappears, and the practice UI runs in Anki itself.

## What Changes

- New Anki addon (Python, `aqt`/`anki` APIs) providing a single QWebEngine practice dialog with four modes: listening, speaking, reading, writing — a full port of the four practice pages from the reference apps.
- Articles become Anki notes of an addon-provisioned `Article` note type (Title, Content, Translation, Url + four per-skill progress fields), stored in a dedicated deck. Article notes generate cards that are **auto-suspended** so articles never enter the review queue.
- Skill progress (`last_line_position` per skill) stored as four separate integer fields on the article note; written **only on extraction** — never on scroll and never on dialog close. No progress-percent display in v1 (progress surfaces only inside the practice dialog, driving learned-line styling and scroll restore).
- Article content/translation fields use `<br>`-canonical line separation with a tolerant parser (`<br>` first, `\n` fallback) so edits made in Anki's rich editor round-trip safely.
- Entry point is Browser-native: right-click an article note → "Practice: Listening/Speaking/Reading/Writing". No separate homepage dialog in v1; ingestion is manual entry/edit inside Anki (no importer, no browser-extension bridge).
- Extract flow (select text → `Ctrl+E`) replaces AnkiConnect `guiAddCards` with direct construction of a note and `NewAddCards.set_note()`, preserving the reference app's per-mode field format: **reading** — Front = source context + `<mark>` + hidden timestamp, Back = Youdao definition (fallback: translation line); **writing** — selection on the translation, Front built from translation lines, Back = source line at the same index; **listening** — selection masked as `???` in Front, Back = selected text, `Phone` = Youdao phonetics; **speaking** — `<mark>` Front, Back = selected text, `Phone` = phonetics. Targets: deck `English`, note types `@Basic` / `@EnListen` / `@EnSpeak` (audio types carry the extra `Phone` field). Missing note types and deck are auto-provisioned on first use; existing ones are adopted by name.
- Youdao dictionary lookup ported from Dart to Python `urllib` against `https://dict.youdao.com/jsonapi?q=<word>` (no API key; empty result on failure).
- TTS reuses Anki's built-in `aqt.tts` machinery (`TTSProcessPlayer`, SAPI on Windows) instead of spawning PowerShell, with a thin adapter to speak arbitrary line text.

## Capabilities

### New Capabilities

- `article-storage`: Article note type schema, deck, auto-provisioning, auto-suspended article cards, `<br>`-canonical line storage, and per-skill progress fields with their write policy.
- `practice-dialog`: Browser context-menu entry, the shared QWebEngine practice dialog with four skill modes, line rendering/selection, learned-line styling, and scroll-position save/restore.
- `practice-extract`: Text selection → `Ctrl+E` extraction, Front/Back/Title/Url field construction, Youdao lookup with translation-line fallback, and prefilled Add-dialog handoff.
- `tts-audio`: Line-level English TTS playback inside the practice dialog via Anki's built-in TTS engine, including voice reuse and content-hash caching.

### Modified Capabilities

(None — this is a greenfield repository; no existing specs.)

## Impact

- **New code**: addon package in this repo (`__init__.py` entry, dialog/UI modules, note-type provisioning, field parsers/builders, Youdao client, TTS adapter). No existing project code is modified.
- **Anki internals depended on**: `aqt.dialogs` / `NewAddCards.set_note`, `gui_hooks.browser_will_show_context_menu`, `aqt.tts` / `aqt.sound`, `anki.notes` / `anki.models` / `anki.decks` APIs — verified present in the installed Anki 26.8.1 (exact signatures to be confirmed at runtime).
- **Collection schema**: new note type + deck created on first use; four progress fields are modified on article notes (sync traffic, last-writer-wins field conflicts across devices).
- **Reference project** `../my_english_ankier_flutter`: read-only source of behavior (11 specs) — not modified.
- **Removed dependency**: no AnkiConnect requirement for this addon's flows (other apps may still use it).
