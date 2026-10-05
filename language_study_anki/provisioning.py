"""Idempotent provisioning of note types and decks.

Specs: article-storage → Auto-provisioning of note types and deck.
Two stages, each gated by a user confirmation (the UI layer in
``provisioning_ui`` asks before calling in):

  article — ``LSA-Article`` note type, offered at profile open
  extract — ``@Basic``/``@EnListen``/``@EnSpeak`` + deck ``English``,
            offered at extraction time

Resolve-by-name first (adopt existing), create only when missing. No
article deck is provisioned (design D6: suspension alone keeps articles
out of review; nothing consumes an article deck).
"""

from __future__ import annotations

ARTICLE_NOTE_TYPE = "LSA-Article"
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


def missing_items(col, scope: str) -> dict:
    """Names absent from the collection for one provisioning scope.

    A pure read — nothing is created — so the UI layer can list exactly
    what a confirmation would add (design D5).
    """
    if scope == "article":
        note_types = [ARTICLE_NOTE_TYPE]
        decks: list[str] = []
    elif scope == "extract":
        note_types = list(EXTRACT_NOTE_TYPES)
        decks = [EXTRACT_DECK]
    else:
        raise ValueError(f"unknown provisioning scope: {scope!r}")
    return {
        "note_types": [n for n in note_types if col.models.by_name(n) is None],
        "decks": [d for d in decks if col.decks.by_name(d) is None],
    }


def build_confirm_message(missing: dict) -> str:
    """The item lines of the confirmation dialog: exactly the missing note
    types and decks, never items that already exist. Empty when nothing is."""
    lines = []
    if missing["note_types"]:
        lines.append("Note types: " + ", ".join(missing["note_types"]))
    if missing["decks"]:
        lines.append("Decks: " + ", ".join(missing["decks"]))
    return "\n".join(lines)


def provision_scope(col, scope: str) -> dict:
    """Provision one scope idempotently; returns its resolved objects/ids."""
    if scope == "article":
        return {"article_notetype": ensure_article_notetype(col)}
    if scope == "extract":
        for name in EXTRACT_NOTE_TYPES:
            ensure_extract_notetype(col, name)
        return {
            "extract_notetypes": {
                name: col.models.by_name(name) for name in EXTRACT_NOTE_TYPES
            },
            "extract_deck_id": ensure_deck(col, EXTRACT_DECK),
        }
    raise ValueError(f"unknown provisioning scope: {scope!r}")


def provision(col) -> dict:
    """Full provisioning (self-test entry), idempotent. Returns resolved
    objects/ids; carries no article deck (design D6)."""
    result = provision_scope(col, "article")
    result.update(provision_scope(col, "extract"))
    return result
