## ADDED Requirements

### Requirement: Legacy extract note types are never adopted
The system SHALL recognize and provision the extract target note types exclusively under the names `LSA-ReadWrite`, `LSA-Listen`, and `LSA-Speak`. Pre-existing note types carrying the legacy names (`@Basic`, `@EnListen`, `@EnSpeak`) SHALL be left untouched: the system SHALL NOT rename them, adopt them, or migrate their notes, and any collection containing only legacy types SHALL be treated as missing the extract targets.

#### Scenario: Collection has only legacy extract types
- **WHEN** the user extracts from a collection that contains note types named `@Basic`, `@EnListen`, or `@EnSpeak` but not the corresponding `LSA-*` types
- **THEN** the extraction-time confirmation lists the missing `LSA-*` note types, and accepting creates them without renaming or modifying the legacy note types

#### Scenario: Legacy notes stay on legacy types
- **WHEN** the user extracts after the `LSA-*` types have been provisioned in a collection that previously held notes on the legacy types
- **THEN** the new note is created on the `LSA-*` note type, and the legacy notes remain attached to their legacy note types unchanged

## MODIFIED Requirements

### Requirement: Auto-provisioning of note types and deck
The system SHALL provision its note types and decks in two stages, each gated by user confirmation. At profile open, when the `LSA-Article` note type is missing, the system SHALL show one confirmation dialog listing exactly the missing items and create them only when the user accepts. At extraction time, when the extract target note types (`LSA-ReadWrite`, `LSA-Listen`, `LSA-Speak`) or target deck (`English`) are missing, the system SHALL show the same kind of confirmation before creating them, and declining cancels the extraction. Existing note types and decks SHALL be adopted by exact name when present, and provisioning SHALL be idempotent. The system SHALL NOT create or require a dedicated article deck.

#### Scenario: First use on a clean collection
- **WHEN** the user opens a profile for the first time in a collection lacking the `LSA-Article` note type
- **THEN** the system shows one confirmation dialog listing exactly the missing items, and creates them once the user accepts, without further setup

#### Scenario: Nothing missing at profile open
- **WHEN** a profile opens and the `LSA-Article` note type already exists
- **THEN** no dialog is shown and nothing is created

#### Scenario: Startup confirmation declined
- **WHEN** the user declines the startup confirmation dialog
- **THEN** nothing is created at that moment, and the same confirmation is offered again at the next profile open

#### Scenario: Extract targets created at extraction time
- **WHEN** the user extracts a selection and any extract target note type or the `English` deck is missing
- **THEN** the system shows a confirmation listing exactly the missing items before creating anything

#### Scenario: Extract-time confirmation declined
- **WHEN** the user declines the extraction-time confirmation
- **THEN** extraction is cancelled: no Add dialog opens and no note is created

#### Scenario: Headless self-test runs unattended
- **WHEN** the addon runs under its self-test harness
- **THEN** provisioning proceeds automatically without displaying any confirmation dialog

#### Scenario: Existing note types are adopted
- **WHEN** the collection already contains note types named `LSA-ReadWrite`, `LSA-Listen`, or `LSA-Speak`, or decks named `English`
- **THEN** the system uses those existing note types and decks instead of creating duplicates
