"""Idempotent provisioning of note types and decks.

Specs: article-storage → Auto-provisioning of note types and deck.
Decision D7: resolve-by-name first (adopt existing), create only when missing.
"""

from __future__ import annotations

ARTICLE_NOTE_TYPE = "LSA-Article"
ARTICLE_DECK = "Articles"
EXTRACT_DECK = "English"
EXTRACT_NOTE_TYPES = ["@Basic", "@EnListen", "@EnSpeak"]
EXTRACT_FIELD_NAMES = ["Front", "Back", "Title", "Url"]
ARTICLE_FIELDS = [
    "Title",
    "Content",
    "Translation",
    "Url",
    "ProgListening",
    "ProgSpeaking",
    "ProgReading",
    "ProgWriting",
]
# Audio extract types carry an extra phonetics field (reference behavior).
AUDIO_EXTRACT_NOTE_TYPES = ("@EnListen", "@EnSpeak")


def required_extract_fields(name: str) -> list[str]:
    fields = list(EXTRACT_FIELD_NAMES)
    if name in AUDIO_EXTRACT_NOTE_TYPES:
        fields.append("Phone")
    return fields
# Extraction target per practice mode (spec: practice-extract).
MODE_NOTETYPE = {
    "reading": "@Basic",
    "writing": "@Basic",
    "listening": "@EnListen",
    "speaking": "@EnSpeak",
}


def _create_article_model(mm) -> dict:
    model = mm.new(ARTICLE_NOTE_TYPE)
    for field in ARTICLE_FIELDS:
        mm.add_field(model, mm.new_field(field))
    tmpl = mm.new_template("Article card")
    tmpl["qfmt"] = "{{Title}}"
    tmpl["afmt"] = '{{FrontSide}}<hr id="answer">{{Content}}'
    mm.add_template(model, tmpl)
    model["sortf"] = 0  # Title is the sort field
    mm.add(model)
    return mm.by_name(ARTICLE_NOTE_TYPE)


def _create_extract_model(mm, name: str) -> dict:
    model = mm.new(name)
    for field in required_extract_fields(name):
        mm.add_field(model, mm.new_field(field))
    tmpl = mm.new_template("Card 1")
    tmpl["qfmt"] = "{{Front}}"
    tmpl["afmt"] = '{{FrontSide}}<hr id="answer">{{Back}}'
    mm.add_template(model, tmpl)
    mm.add(model)
    return mm.by_name(name)


def ensure_article_notetype(col) -> dict:
    mm = col.models
    return mm.by_name(ARTICLE_NOTE_TYPE) or _create_article_model(mm)


def ensure_extract_notetype(col, name: str) -> dict:
    """Resolve-by-name, create if missing — and guarantee the spec'd field
    set (Front/Back/Title/Url): an adopted foreign note type may lack fields
    the extract flow writes (evidence: decoy @EnSpeak without 'Back' raised
    KeyError). Additive only — never removes or renames user fields."""
    mm = col.models
    model = mm.by_name(name) or _create_extract_model(mm, name)
    existing = {f["name"] for f in model["flds"]}
    changed = False
    for field in required_extract_fields(name):
        if field not in existing:
            mm.add_field(model, mm.new_field(field))
            changed = True
    if changed:
        if hasattr(mm, "update_dict"):
            mm.update_dict(model)
        model = mm.by_name(name) or model
    return model


def ensure_deck(col, name: str) -> int:
    """Deck id, creating the deck if missing (``decks.id`` is idempotent)."""
    return int(col.decks.id(name))


def provision(col) -> dict:
    """Provision everything, idempotently. Returns resolved objects/ids."""
    ensure_article_notetype(col)
    for name in EXTRACT_NOTE_TYPES:
        ensure_extract_notetype(col, name)
    return {
        "article_notetype": col.models.by_name(ARTICLE_NOTE_TYPE),
        "article_deck_id": ensure_deck(col, ARTICLE_DECK),
        "extract_notetypes": {
            name: col.models.by_name(name) for name in EXTRACT_NOTE_TYPES
        },
        "extract_deck_id": ensure_deck(col, EXTRACT_DECK),
    }
