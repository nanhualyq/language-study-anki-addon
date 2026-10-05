## MODIFIED Requirements

### Requirement: Auto-provisioning of note types and deck
The system SHALL provision its note types and decks in two stages, each gated by user confirmation. At profile open, when the `LSA-Article` note type is missing, the system SHALL show one confirmation dialog listing exactly the missing items and create them only when the user accepts. At extraction time, when the extract target note types (`@Basic`, `@EnListen`, `@EnSpeak`) or target deck (`English`) are missing, the system SHALL show the same kind of confirmation before creating them, and declining cancels the extraction. Existing note types and decks SHALL be adopted by exact name when present, and provisioning SHALL be idempotent. The system SHALL NOT create or require a dedicated article deck.

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
- **WHEN** the collection already contains note types named `@Basic`, `@EnListen`, or `@EnSpeak`, or decks named `English`
- **THEN** the system uses those existing note types and decks instead of creating duplicates

### Requirement: Articles never enter the review queue
The system SHALL ensure each article note's generated card is suspended at creation time, so articles never appear during study. Article residence in any particular deck SHALL NOT be required or enforced.

#### Scenario: Article note created
- **WHEN** the system creates an article note
- **THEN** the card generated from the note is suspended

#### Scenario: Article note edited
- **WHEN** an existing article note is edited such that its card would be regenerated or unsuspended
- **THEN** the article's card remains suspended and excluded from review queues after the edit
