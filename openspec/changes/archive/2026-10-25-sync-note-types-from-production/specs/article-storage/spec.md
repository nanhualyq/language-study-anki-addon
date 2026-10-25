## MODIFIED Requirements

### Requirement: Article note type
The system SHALL represent an article as an Anki note of an addon-provisioned `LSA-Article` note type with fields `Title`, `Content`, `Translation`, `Url`, `ProgListening`, `ProgSpeaking`, `ProgReading`, `ProgWriting`, and `Cover`. `Title` SHALL be the sort field. `Translation`, `Url`, and `Cover` MAY be empty.

#### Scenario: Store an article with all fields
- **WHEN** the user creates an article note with a title, English content, a Chinese translation, and a URL
- **THEN** the system stores all values in the corresponding fields of a single note

#### Scenario: Store an article without translation or URL
- **WHEN** the user creates an article note with a title and English content only
- **THEN** the `Translation` and `Url` fields are stored as empty strings

#### Scenario: Store an article without a cover
- **WHEN** the user creates an article note without a cover image reference
- **THEN** the `Cover` field is stored as an empty string, and the note is otherwise complete
