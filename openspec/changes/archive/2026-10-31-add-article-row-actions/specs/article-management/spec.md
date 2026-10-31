## Purpose

Covers the lifecycle actions for article notes — add, edit, duplicate-as-new,
and delete — and the native Anki dialog each action drives, so the article
library can be managed entirely from the article list.

## ADDED Requirements

### Requirement: Add an article
The list page's add entry SHALL open Anki's native Add dialog holding a
fresh `LSA-Article` note with all fields empty and no deck requirement beyond
the dialog's normal deck choice. No note SHALL be created until the user
confirms the dialog; closing the dialog without confirming SHALL leave the
collection unchanged. A note created through the dialog SHALL have its card
suspended so it never enters the review queue. The four progress fields
SHALL NOT be prefilled by the system.

#### Scenario: Add and confirm
- **WHEN** the user activates the add entry, fills in a title and content,
  and confirms the dialog
- **THEN** a new `LSA-Article` note exists with those values, its progress
  fields empty, and its card suspended

#### Scenario: Add and abandon
- **WHEN** the user activates the add entry and closes the dialog without
  confirming
- **THEN** no note is created

#### Scenario: Add never prefills progress
- **WHEN** the add dialog opens
- **THEN** the four progress fields are empty regardless of any article's
  stored progress

### Requirement: Edit an article in place
The row's edit entry SHALL open Anki's native note-editing dialog (the
reviewer's Edit Current dialog) for that row's article note. Saving SHALL
update the note in place: the note id SHALL NOT change, the four progress
fields SHALL NOT be written by the system, and the article's card SHALL
remain suspended after the save. Closing the dialog without saving SHALL
leave the note unchanged.

#### Scenario: Edit and save
- **WHEN** the user opens edit for an article, changes its content, and
  saves
- **THEN** the same note holds the new content, its note id and progress
  values are unchanged, and its card is still suspended

#### Scenario: Edit preserves progress
- **WHEN** the user saves an edit without touching the progress fields
- **THEN** every progress field keeps its previous value and the list's
  percentages are computed from those values

#### Scenario: Card stays suspended after edit
- **WHEN** an edited article note is saved
- **THEN** the article's card remains suspended and excluded from review
  queues

### Requirement: Duplicate an article as new
The row's duplicate-as-new entry SHALL open Anki's native Add dialog holding
a new note prefilled from the source article: `Title` equal to the source
title suffixed with ` (Copy)`, `Content`, `Translation`, `Url`, and `Cover`
equal to the source values, and the four progress fields empty. The source
note SHALL NOT be modified. No note SHALL be created until the user confirms
the dialog; closing the dialog without confirming SHALL leave the collection
unchanged. A note created through the dialog SHALL have its card suspended.

#### Scenario: Duplicate prefills copied fields with fresh progress
- **WHEN** the user activates duplicate-as-new on an article titled `X` with
  non-zero progress
- **THEN** the Add dialog opens holding a new note titled `X (Copy)` whose
  `Content`, `Translation`, `Url`, and `Cover` match the source and whose
  four progress fields are empty

#### Scenario: Duplicate and confirm
- **WHEN** the user confirms the duplicate's Add dialog
- **THEN** a new suspended-card article note exists with the prefilled
  values, and the source note is unchanged

#### Scenario: Duplicate and abandon
- **WHEN** the user closes the duplicate's Add dialog without confirming
- **THEN** no note is created and the source note is unchanged

### Requirement: Delete an article
The row's delete entry SHALL show a confirmation dialog naming the article
before anything is removed. Confirming SHALL remove the article's note and
its cards from the collection; declining SHALL change nothing. Deletion
SHALL NOT touch any other note.

#### Scenario: Delete after confirmation
- **WHEN** the user confirms the delete dialog for an article
- **THEN** that note and its cards no longer exist in the collection while
  all other articles are unchanged

#### Scenario: Delete declined
- **WHEN** the user declines the delete dialog
- **THEN** the note remains in the collection unchanged

### Requirement: Actions require the article note type
Add and duplicate-as-new SHALL require the `LSA-Article` note type. When it
is missing, the system SHALL offer the existing provisioning confirmation
before creating it, and declining that confirmation SHALL cancel the action
without creating anything.

#### Scenario: Provisioning declined cancels the action
- **WHEN** the user activates add or duplicate-as-new while `LSA-Article` is
  missing and declines the provisioning confirmation
- **THEN** no note type is created, no dialog opens, and no note is created
