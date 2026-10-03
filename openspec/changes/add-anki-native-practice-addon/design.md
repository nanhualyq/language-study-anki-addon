## Context

See proposal.md for motivation. This repository is greenfield (no code yet). The behavior being ported is defined by `../my_english_ankier_flutter` (3,390 lines of Dart + 11 specs); this change is a native Anki addon targeting the installed Anki 26.8.1 (Python 3.13, PyQt6).

Key verified facts about the target platform (from inspecting the installed Anki's `app_packages`):

- `aqt.addcards.NewAddCards.set_note(note, deck_id=..., original_note_id=...)` exists — the Add dialog accepts a pre-built note.
- `gui_hooks.browser_will_show_context_menu` exists in `aqt.browser.table` — Browser context-menu injection is supported.
- `aqt.tts` implements `TTSProcessPlayer` invoking `SAPI.SpVoice` on Windows, with voice enumeration and hash-based audio caching (`temp_file_for_tag_and_voice`).

The addon runs inside the Anki process: no AnkiConnect, no separate storage, no external TTS process of our own.

## Goals / Non-Goals

**Goals:**

- Port the four practice modes, extract flow, and scroll/progress behavior of the Flutter reference into an in-process Anki addon with fidelity to its 11 specs.
- Keep the collection the single source of truth: articles, progress, and extracted notes all live in it and sync with it.
- Be self-contained: auto-provision note types/decks, adopt user-made ones by name, degrade gracefully on network/TTS failure.

**Non-Goals:**

- Importers, browser-extension bridges, or any ingestion other than manual entry/edit inside Anki (v1).
- A separate "practice library" homepage dialog; the Browser is the homepage.
- Progress percentage display, cross-device progress merging, or scroll-throttled writes.
- Kokoro/cloud TTS, Linux/macOS TTS parity (Windows/SAPI is the reference environment; the adapter should not preclude others).
- Modifying the reference apps or exporting from their databases.

## Decisions

### D1. Articles as notes; progress as four separate fields

Alternatives: progress in one combined field; progress in an addon-local DB; articles as plain rows in an addon DB.

Chosen: `Article` note type with `Title` (sort), `Content`, `Translation`, `Url`, and `ProgListening/ProgSpeaking/ProgReading/ProgWriting`.

- Rationale: user decision (explore session) — collection sync for free, no second store.
- Four fields instead of one combined `Progress` field: each skill's update rewrites only its own field, so cross-device sync conflicts isolate to one skill (spec: *Per-skill progress fields*).
- Values are raw 1-based line numbers (Flutter parity; percent needs `total_lines` and would churn on content edits).

### D2. Auto-suspended article cards (vs. card deletion)

Alternatives: delete generated card after creation (must be re-applied on every note edit via hooks); template that never matches (Anki regenerates cards on field edits); let articles be real review cards.

Chosen: suspend the generated card at creation and after edits, in a dedicated deck.

- Rationale: suspension is first-class collection state, syncs, survives edits, one-line enforcement. Deletion is cleaner conceptually but fragile against Anki's card-regeneration rules.
- Enforcement points: after note creation, and via a note-update hook to cover edits made in Anki's own editor.

### D3. `<br>`-canonical line storage with tolerant parser

Alternatives: `\n` storage with a "don't edit in Anki" rule; spike-then-decide.

Chosen: write `<br>` as the canonical separator; parse `<br>` first, fall back to `\n`, tolerate editor artifacts (`<p>`, `<div>`, `<br/>`).

- Rationale: Anki's rich editor round-trips multi-line content as HTML; `<br>` storage survives user edits, which is the only line-integrity risk that silently shifts `last_line_position` semantics.
- The parser is the single code path used by all four modes, extraction context building, and progress clamping — one place to keep correct.

### D4. One QWebEngine dialog, four modes, mode as a rendering flag

Alternatives: four separate page implementations (Flutter parity: four `*_practice_page.dart` files).

Chosen: a single dialog + HTML/JS renderer parameterized by mode; Python side handles selection capture (JS → Python bridge), progress I/O, TTS requests, and extraction.

- Rationale: the four Flutter pages differ only in per-line visibility rules and which note type extraction targets (verified by reading all four). Line rendering, selection, scroll restore, and learned-line styling are identical logic — porting them once removes the `skill_progress_sync`-style duplication the Flutter app needed Riverpod for (irrelevant here: one window, direct calls).
- Qt widget text selection was rejected: no practical way to get selection ranges + line numbers; web selection is the reference behavior.

### D5. TTS via `aqt.tts` (adapter), not PowerShell

Alternatives: port the PowerShell/System.Speech module from Flutter/Electrobun; Kokoro server.

Chosen: drive Anki's `TTSProcessPlayer`/AVPlayer with plain line text via a thin adapter.

- Rationale: same voices + settings the user already has in Anki, built-in caching by content hash (the Flutter app hand-rolled exactly this), no second synthesis path in-process.
- The engine is tag-oriented (`TTSTag`), so the adapter normalizes "speak this string" into the engine's expected form.

### D6. Extract = construct `anki.notes.Note` + `NewAddCards.set_note`

Alternatives: keep AnkiConnect (pointless in-process); add the note directly without the dialog (loses the reference's confirm/edit-before-add step).

Chosen: build the note (field format per spec: 3-line context + `<mark>` + hidden timestamp, `<br>` separators, Youdao → translation-line fallback), open `AddCards` via `aqt.dialogs`, call `set_note`.

- Rationale: preserves the Flutter UX exactly (user always confirms in the Add dialog), removes the entire HTTP service layer. Youdao stays external HTTP but moves to `urllib` with timeout → empty result.
- Deck/note types resolved by name once per session through the provisioning layer (D7), cached by ID.

### D7. Idempotent provisioning by name

Alternatives: hard-fail with "missing note type" (user must fix manually); silently create duplicates.

Chosen: resolve-by-name → create-if-missing, for `Article` + article deck, `@Basic`/`@EnListen`/`@EnSpeak` + `English`. Provisions lazily on first use (Browser menu / first extract), not at addon load.

- Rationale: zero-setup install; user-made types with the same name are adopted (the reference assumes `@Basic` etc. already exist in the user's collection).

### D8. Progress write policy: extract only

Alternatives: extract + dialog close (an earlier draft — rejected by user decision); throttled scroll writes (sync churn, no semantic value).

Chosen: write the mode's progress field only when an extraction happens from line N (monotonic: set to at least N). Scrolling and dialog close never write.

- Rationale: minimal sync churn and the semantically precise definition — progress means "last extracted line" (user decision). Known trade-off: skills where the user never extracts (notably listening/speaking) record no progress; accepted for v1. Sync conflicts bounded by D1's field isolation; writes are rare (per extract only).

## Risks / Trade-offs

- [`NewAddCards.set_note` exact signature/behavior differs from bytecode strings] → First implementation task is a runtime spike against Anki 26.8.1; fallback: open the Add dialog and set fields via its editor API (`editor.set_note`/fields area), which the bytecode also shows. Specs only constrain observable behavior (dialog opens prefilled), so either path satisfies them.
- [`aqt.tts` adapter proves hard to drive for plain text] → Spike task before building the dialog; fallback is a subprocess System.Speech player behind the same interface the dialog consumes — specs constrain caching/non-blocking behavior, not the engine.
- [Anki's rich editor rewrites `<br>` content in an unexpected form (e.g., wraps lines in `<p>`)] → Verify with a manual round-trip task early; tolerant parser (D3) designed to absorb `<p>`/`<div>`/`\n`; if verification fails, parser normalization is the single fix point.
- [Sync conflicts on progress fields: last-writer-wins, no merge] → Accepted (user decision); four-field isolation (D1) bounds blast radius to one skill; monotonic writes (D8) limit regression frequency.
- [Suspended-card invariant broken by note-type edits (user edits `Article` template, Anki re-enables cards)] → Note-update hook re-suspends; low frequency, cheap check.
- [Cardless/suspended notes flagged by Anki's "Check Database" / empty-cards] → Suspended cards are valid collection state; empty-cards check only flags cards with empty templates — the `Article` template renders non-empty content. Verify during provisioning spike.
- [`Ctrl+E` collides with an Anki/Browser shortcut] → Bind in the dialog's webview only (scoped to practice window, not global); verify against Anki's existing shortcuts during UI task.
- [Youdao API changes or rate-limits] → Already spec'd: failures degrade to translation-line fallback; extraction never blocks on it (timeout in the client).
- [Fidelity drift from the Flutter reference (11 specs)] → Port behavior from specs, not just code; where the reference is ambiguous, its spec text is authoritative.

## Migration Plan

Greenfield — no migration. Rollback = remove the addon directory; the only collection residue is the `Article`/extract note types, the article/`English` deck entries, and notes the user created (all inert without the addon; safely deletable via Anki's normal tools).

## Open Questions

- None that block implementation. The three runtime unknowns (set_note surface, TTS adapter drivability, editor round-trip) are verification tasks in tasks.md, not spec- or design-changing questions.
