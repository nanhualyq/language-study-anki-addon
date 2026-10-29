# Design: add-article-cover-to-list

## Applicability

This document is minimal by design: the change does not meet any of the
inclusion triggers (cross-cutting change, new external dependency, security /
performance / migration complexity, or ambiguity needing technical decisions
before coding). It is a single-module change (`hub.py` payload + `list.html`
template) whose two technical choices were settled during exploration with the
user; they are recorded here for traceability.

## Decisions

- **Thumbnail sizing**: fixed `max-height` with intrinsic aspect ratio and
  `object-fit: cover` crop. Chosen over a fixed width×height box because
  cover images have varying aspect ratios and a fixed box distorts them.
- **Empty/absent `Cover`**: render the row's existing title-and-skills layout
  with no thumbnail and no placeholder. Chosen over a placeholder because the
  fallback is rare in practice and a placeholder adds visual noise.
- **Raw HTML pass-through**: `Cover` holds editor-pasted `<img>` HTML; it is
  rendered as-is (not escaped) — the same trust level as the card templates
  that already render `{{Cover}}`.
