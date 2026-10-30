"""Idempotent provisioning of note types and decks.

Specs: article-storage → Auto-provisioning of note types and deck.
Two stages, each gated by a user confirmation (the UI layer in
``provisioning_ui`` asks before calling in):

  article — ``LSA-Article`` note type, offered at profile open
  extract — ``LSA-ReadWrite``/``LSA-Listen``/``LSA-Speak`` + deck ``English``,
            offered at extraction time

Resolve-by-name first (adopt existing), create only when missing. No
article deck is provisioned (design D6: suspension alone keeps articles
out of review; nothing consumes an article deck).
"""

from __future__ import annotations

ARTICLE_NOTE_TYPE = "LSA-Article"
EXTRACT_DECK = "English"
EXTRACT_NOTE_TYPES = ["LSA-ReadWrite", "LSA-Listen", "LSA-Speak"]

# Production is the source of truth (captured 2026-10-25). Field order below
# matches it exactly; ``Cover`` is provisioned on every type including the
# article. ``required_extract_fields`` returns the ordered production list —
# its additive-repair role only checks membership, never reorders.
EXTRACT_FIELD_NAMES = ["Front", "Back", "Url", "Title", "Cover"]
STICKY_EXTRACT_FIELDS = frozenset({"Front", "Back", "Url", "Title"})
ARTICLE_FIELDS = [
    "Title",
    "Content",
    "Translation",
    "Url",
    "ProgListening",
    "ProgSpeaking",
    "ProgReading",
    "ProgWriting",
    "Cover",
]
# Audio extract types carry an extra phonetics field (reference behavior);
# production places ``Phone`` third, right after ``Back``.
AUDIO_EXTRACT_NOTE_TYPES = ("LSA-Listen", "LSA-Speak")


def required_extract_fields(name: str) -> list[str]:
    fields = list(EXTRACT_FIELD_NAMES)
    if name in AUDIO_EXTRACT_NOTE_TYPES:
        fields.insert(2, "Phone")
    return fields
# Extraction target per practice mode (spec: practice-extract).
MODE_NOTETYPE = {
    "reading": "LSA-ReadWrite",
    "writing": "LSA-ReadWrite",
    "listening": "LSA-Listen",
    "speaking": "LSA-Speak",
}


# Production note-type styling / templates (captured 2026-10-25).
_CSS_ARTICLE = (
    ".card {\n"
    "    font-family: arial;\n"
    "    font-size: 20px;\n"
    "    line-height: 1.5;\n"
    "    text-align: center;\n"
    "    color: black;\n"
    "    background-color: white;\n"
    "}\n"
)
_CSS_EXTRACT = (
    ".card {\n"
    "    font-family: arial;\n"
    "    font-size: 20px;\n"
    "    text-align: center;\n"
    "    color: black;\n"
    "    background-color: white;\n"
    "}\n"
)
# Shared gray metadata header on every extract card question.
_CARD_HEADER = (
    '<p style="font-size: small; color: gray;">\n'
    "{{Deck}} {{#Tags}}#{{Tags}}{{/Tags}}\n"
    "{{#Title}} <br>{{Title}} {{/Title}}\n"
    '{{#Url}} <br><a href="{{Url}}">{{Url}}</a> {{/Url}}\n'
    "</p>\n\n"
)
# The cover is wrapped in <p> so it keeps paragraph spacing from the
# Front/TTS text above (the earlier <br> variant rendered it glued to
# that text).
_COVER_BLOCK = "{{#Cover}}<p>{{Cover}}</p>{{/Cover}}\n"
EXTRACT_TEMPLATES = {
    "LSA-ReadWrite": {
        "qfmt": _CARD_HEADER + "{{Front}}\n\n" + _COVER_BLOCK,
        "afmt": "{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}\n",
    },
    "LSA-Listen": {
        "qfmt": _CARD_HEADER + "{{Front}}\n<br>\n{{tts en_US :Back}}\n\n" + _COVER_BLOCK,
        "afmt": "{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}\n\n<p>{{Phone}}</p>",
    },
    "LSA-Speak": {
        "qfmt": _CARD_HEADER + "{{Front}}\n\n" + _COVER_BLOCK,
        "afmt": "{{FrontSide}}\n\n<hr id=answer>\n\n{{tts en_US :Back}}\n\n<p>{{Phone}}</p>",
    },
}
_EXTRACT_BROWSER_QFMT = "{{Front}}"


def _create_article_model(mm) -> dict:
    model = mm.new(ARTICLE_NOTE_TYPE)
    for field in ARTICLE_FIELDS:
        mm.add_field(model, mm.new_field(field))
    tmpl = mm.new_template("Article card")
    tmpl["qfmt"] = "{{Title}}"
    tmpl["afmt"] = '{{FrontSide}}<hr id="answer">{{Content}}'
    mm.add_template(model, tmpl)
    model["sortf"] = 0  # Title is the sort field
    model["css"] = _CSS_ARTICLE
    mm.add(model)
    return mm.by_name(ARTICLE_NOTE_TYPE)


def _create_extract_model(mm, name: str) -> dict:
    model = mm.new(name)
    for field in required_extract_fields(name):
        fld = mm.new_field(field)
        fld["sticky"] = field in STICKY_EXTRACT_FIELDS
        mm.add_field(model, fld)
    tmpl = mm.new_template("Card 1")
    spec = EXTRACT_TEMPLATES[name]
    tmpl["qfmt"] = spec["qfmt"]
    tmpl["afmt"] = spec["afmt"]
    tmpl["bqfmt"] = _EXTRACT_BROWSER_QFMT
    mm.add_template(model, tmpl)
    model["sortf"] = 0  # Front is the sort field
    model["css"] = _CSS_EXTRACT
    mm.add(model)
    return mm.by_name(name)


def ensure_article_notetype(col) -> dict:
    mm = col.models
    return mm.by_name(ARTICLE_NOTE_TYPE) or _create_article_model(mm)


def ensure_extract_notetype(col, name: str) -> dict:
    """Resolve-by-name, create if missing — and guarantee the spec'd field
    set (Front/Back/Title/Url/Cover): an adopted foreign note type may lack
    fields the extract flow writes (evidence: decoy LSA-Speak without 'Back'
    raised KeyError). Additive only — never removes or renames user fields."""
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
