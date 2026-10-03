## Purpose

Speaks English practice lines aloud inside the practice dialog by reusing Anki's built-in TTS engine, so playback uses the voices and caching the user already has in Anki instead of an external process.

## ADDED Requirements

### Requirement: Line text playback
The system SHALL speak arbitrary English line text from the practice dialog using Anki's built-in TTS engine (system voices; SAPI on Windows), with playback started from the per-line play button in Listening and Speaking modes.

#### Scenario: Play a line
- **WHEN** the user clicks the play button on a line in Listening or Speaking mode
- **THEN** the line's text is spoken aloud using the engine's configured voice

#### Scenario: Playback failure
- **WHEN** the TTS engine fails to produce audio for a line
- **THEN** the failure is handled without crashing the dialog, and the user receives non-blocking feedback

### Requirement: Repeated text is not re-synthesized
The system SHALL cache synthesized audio keyed by the text content (and voice), so requesting the same line twice reuses the cached result rather than synthesizing again.

#### Scenario: Same line played twice
- **WHEN** the user plays the same line text twice in one session or across sessions
- **THEN** the second playback reuses the cached audio instead of re-synthesizing

### Requirement: Non-blocking playback during practice
TTS synthesis and playback SHALL NOT block the practice dialog's UI: line rendering, scrolling, selection, and extraction remain responsive while audio plays, and starting a new line's playback SHALL stop the current one.

#### Scenario: Play while scrolling
- **WHEN** audio is playing and the user scrolls or selects text
- **THEN** the dialog stays responsive and the interaction completes normally

#### Scenario: Rapid successive playback
- **WHEN** the user clicks play on a second line while the first is still playing
- **THEN** the first playback stops and the second line's audio starts
