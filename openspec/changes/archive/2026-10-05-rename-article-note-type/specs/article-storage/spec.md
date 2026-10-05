## MODIFIED Requirements

### Requirement: Article note type
The system SHALL represent an article as an Anki note of an addon-provisioned `LSA-Article` note type with fields `Title`, `Content`, `Translation`, `Url`, `ProgListening`, `ProgSpeaking`, `ProgReading`, and `ProgWriting`. `Title` SHALL be the sort field. `Translation` and `Url` MAY be empty.

#### Scenario: Store an article with all fields
- **WHEN** the user creates an article note with a title, English content, a Chinese translation, and a URL
- **THEN** the system stores all values in the corresponding fields of a single note

#### Scenario: Store an article without translation or URL
- **WHEN** the user creates an article note with a title and English content only
- **THEN** the `Translation` and `Url` fields are stored as empty strings

### Requirement: Auto-provisioning of note types and deck
The system SHALL create the `LSA-Article` note type, the dedicated article deck, and the extract target note types (`@Basic`, `@EnListen`, `@EnSpeak`) and target deck (`English`) if they do not already exist, and SHALL adopt existing ones by exact name when present. Provisioning SHALL be idempotent.

#### Scenario: First use on a clean collection
- **WHEN** the user opens the practice entry for the first time in a collection lacking the required note types and decks
- **THEN** the system creates the missing note types and decks before proceeding, without user setup

#### Scenario: Existing note types are adopted
- **WHEN** the collection already contains note types named `@Basic`, `@EnListen`, or `@EnSpeak`, or decks named `English`
- **THEN** the system uses those existing note types and decks instead of creating duplicates
