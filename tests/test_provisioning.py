"""Unit tests for scoped provisioning helpers.

Change: add-startup-provisioning-confirm (spec: article-storage →
Auto-provisioning of note types and deck).

Zero-dependency style like the rest of tests/: provisioning imports
cleanly without aqt. Fakes implement only what the helpers read —
``models.by_name`` / ``decks.by_name`` lookups, nothing else.
"""

from __future__ import annotations

import unittest

from language_study_anki.provisioning import (
    ARTICLE_NOTE_TYPE,
    EXTRACT_DECK,
    EXTRACT_NOTE_TYPES,
    _create_article_model,
    _create_extract_model,
    build_confirm_message,
    ensure_extract_notetype,
    missing_items,
    required_extract_fields,
)


class FakeByName:
    def __init__(self, names=()):
        self._names = set(names)

    def by_name(self, name):
        return {"name": name} if name in self._names else None


class FakeCol:
    def __init__(self, note_types=(), decks=()):
        self.models = FakeByName(note_types)
        self.decks = FakeByName(decks)


class MissingItemsArticleScope(unittest.TestCase):
    def test_empty_collection_reports_article_type_only(self):
        missing = missing_items(FakeCol(), "article")
        self.assertEqual(missing, {"note_types": [ARTICLE_NOTE_TYPE], "decks": []})

    def test_existing_article_type_reports_nothing(self):
        col = FakeCol(note_types=[ARTICLE_NOTE_TYPE])
        self.assertEqual(
            missing_items(col, "article"), {"note_types": [], "decks": []}
        )

    def test_article_scope_never_includes_decks(self):
        # Design D6: no article deck is ever provisioned.
        missing = missing_items(FakeCol(), "article")
        self.assertEqual(missing["decks"], [])


class MissingItemsExtractScope(unittest.TestCase):
    def test_empty_collection_reports_all_extract_targets(self):
        missing = missing_items(FakeCol(), "extract")
        self.assertEqual(
            missing,
            {"note_types": list(EXTRACT_NOTE_TYPES), "decks": [EXTRACT_DECK]},
        )

    def test_partial_presence_reports_only_missing(self):
        col = FakeCol(note_types=["LSA-ReadWrite"], decks=["English"])
        self.assertEqual(
            missing_items(col, "extract"),
            {"note_types": ["LSA-Listen", "LSA-Speak"], "decks": []},
        )

    def test_all_present_reports_nothing(self):
        col = FakeCol(note_types=list(EXTRACT_NOTE_TYPES), decks=[EXTRACT_DECK])
        self.assertEqual(
            missing_items(col, "extract"), {"note_types": [], "decks": []}
        )

    def test_unknown_scope_raises(self):
        with self.assertRaises(ValueError):
            missing_items(FakeCol(), "nope")


class BuildConfirmMessageTest(unittest.TestCase):
    def test_lists_note_types_and_decks(self):
        msg = build_confirm_message(
            {"note_types": ["LSA-ReadWrite"], "decks": [EXTRACT_DECK]}
        )
        self.assertIn("Note types: LSA-ReadWrite", msg)
        self.assertIn(f"Decks: {EXTRACT_DECK}", msg)

    def test_article_scope_omits_deck_line(self):
        msg = build_confirm_message(
            {"note_types": [ARTICLE_NOTE_TYPE], "decks": []}
        )
        self.assertIn(ARTICLE_NOTE_TYPE, msg)
        self.assertNotIn("Decks:", msg)

    def test_lists_all_missing_types_in_order(self):
        msg = build_confirm_message(
            {"note_types": ["LSA-ReadWrite", "LSA-Listen", "LSA-Speak"], "decks": []}
        )
        self.assertIn("Note types: LSA-ReadWrite, LSA-Listen, LSA-Speak", msg)

    def test_never_lists_present_items(self):
        # Only the (already filtered) missing dict is rendered.
        msg = build_confirm_message({"note_types": ["LSA-Speak"], "decks": []})
        self.assertNotIn("LSA-ReadWrite", msg)
        self.assertNotIn("LSA-Listen", msg)

    def test_empty_missing_renders_empty_string(self):
        self.assertEqual(build_confirm_message({"note_types": [], "decks": []}), "")


class RequiredExtractFieldsTest(unittest.TestCase):
    """Spec: practice-extract → every extract type carries Cover; audio
types add Phone (change: rename-extract-note-types-add-cover)."""

    def test_non_audio_type_has_cover_no_phone(self):
        fields = required_extract_fields("LSA-ReadWrite")
        self.assertIn("Cover", fields)
        self.assertNotIn("Phone", fields)

    def test_audio_types_have_cover_and_phone(self):
        for name in ("LSA-Listen", "LSA-Speak"):
            fields = required_extract_fields(name)
            self.assertIn("Cover", fields)
            self.assertIn("Phone", fields)


class _FakeModelMgr:
    """Minimal model manager exercising ensure_extract_notetype's additive
    repair path: by_name / new / add_field / new_field / update_dict only."""

    def __init__(self, models=None):
        self._models = {m["name"]: m for m in (models or [])}

    def by_name(self, name):
        return self._models.get(name)

    def new(self, name):
        return {"name": name, "flds": [], "tmpls": []}

    def new_field(self, name):
        return {"name": name}

    def add_field(self, model, field):
        model["flds"].append(field)

    def new_template(self, name):
        return {"name": name, "qfmt": "", "afmt": ""}

    def add_template(self, model, tmpl):
        model["tmpls"].append(tmpl)

    def add(self, model):
        self._models[model["name"]] = model

    def update_dict(self, model):
        self._models[model["name"]] = model


class _FakeMMCol:
    def __init__(self, mm):
        self.models = mm


class AdoptedTypeAdditiveRepairTest(unittest.TestCase):
    """An adopted foreign extract type missing required fields gets them
    appended additively — including the new Cover field — never renamed or
    removed (mirrors the in-addon decoy-repair check)."""

    def test_adopted_type_missing_cover_gains_it_additively(self):
        decoy = {
            "name": "LSA-Listen",
            "flds": [{"name": "Front"}, {"name": "Back"}],
            "tmpls": [],
        }
        mm = _FakeModelMgr([decoy])
        model = ensure_extract_notetype(_FakeMMCol(mm), "LSA-Listen")
        names = [f["name"] for f in model["flds"]]
        # Original fields preserved, in order
        self.assertEqual(names[:2], ["Front", "Back"])
        for req in ("Title", "Url", "Cover", "Phone"):
            self.assertIn(req, names)
        self.assertEqual(len(names), len(set(names)))  # no duplicates

    def test_freshly_created_type_has_cover(self):
        mm = _FakeModelMgr()
        model = ensure_extract_notetype(_FakeMMCol(mm), "LSA-ReadWrite")
        names = [f["name"] for f in model["flds"]]
        self.assertIn("Cover", names)
        self.assertNotIn("Phone", names)  # non-audio type


# --- production reference literals (captured 2026-10-25) -----------------
_PROD_CSS_EXTRACT = (
    ".card {\n"
    "    font-family: arial;\n"
    "    font-size: 20px;\n"
    "    text-align: center;\n"
    "    color: black;\n"
    "    background-color: white;\n"
    "}\n"
)
_PROD_CSS_ARTICLE = (
    ".card {\n"
    "    font-family: arial;\n"
    "    font-size: 20px;\n"
    "    line-height: 1.5;\n"
    "    text-align: center;\n"
    "    color: black;\n"
    "    background-color: white;\n"
    "}\n"
)
_PROD_HEADER = (
    '<p style="font-size: small; color: gray;">\n'
    "{{Deck}} {{#Tags}}#{{Tags}}{{/Tags}}\n"
    "{{#Title}} <br>{{Title}} {{/Title}}\n"
    '{{#Url}} <br><a href="{{Url}}">{{Url}}</a> {{/Url}}\n'
    "</p>\n\n"
)
# Cover block intentionally diverges from the 2026-10-25 production
# snapshot: the cover is wrapped in <p> (paragraph spacing from the text
# above) instead of the original glued-on <br> variant.
_PROD_COVER = "{{#Cover}}<p>{{Cover}}</p>{{/Cover}}\n"


class ProductionParityTest(unittest.TestCase):
    """A freshly created note type matches the production collection captured
    2026-10-25: field order, sticky flags, card templates, browser template,
    CSS, and sort field (change: sync-note-types-from-production)."""

    def _build(self, name):
        mm = _FakeModelMgr()
        if name == ARTICLE_NOTE_TYPE:
            return _create_article_model(mm)
        return _create_extract_model(mm, name)

    @staticmethod
    def _sticky(model):
        return {f["name"]: f.get("sticky", False) for f in model["flds"]}

    def test_article_parity(self):
        m = self._build(ARTICLE_NOTE_TYPE)
        self.assertEqual(
            [f["name"] for f in m["flds"]],
            [
                "Title", "Content", "Translation", "Url",
                "ProgListening", "ProgSpeaking", "ProgReading", "ProgWriting",
                "Cover",
            ],
        )
        self.assertFalse(any(self._sticky(m).values()))  # none sticky
        self.assertEqual(m["sortf"], 0)  # Title
        self.assertEqual(m["css"], _PROD_CSS_ARTICLE)
        self.assertEqual(m["tmpls"][0]["qfmt"], "{{Title}}")
        self.assertEqual(
            m["tmpls"][0]["afmt"], '{{FrontSide}}<hr id="answer">{{Content}}'
        )

    def test_readwrite_parity(self):
        m = self._build("LSA-ReadWrite")
        self.assertEqual(
            [f["name"] for f in m["flds"]],
            ["Front", "Back", "Url", "Title", "Cover"],
        )
        self.assertEqual(
            self._sticky(m),
            {"Front": True, "Back": True, "Url": True, "Title": True, "Cover": False},
        )
        self.assertEqual(m["sortf"], 0)  # Front
        self.assertEqual(m["css"], _PROD_CSS_EXTRACT)
        t = m["tmpls"][0]
        self.assertEqual(t["qfmt"], _PROD_HEADER + "{{Front}}\n\n" + _PROD_COVER)
        self.assertEqual(t["afmt"], "{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}\n")
        self.assertEqual(t["bqfmt"], "{{Front}}")

    def test_listen_parity(self):
        m = self._build("LSA-Listen")
        self.assertEqual(
            [f["name"] for f in m["flds"]],
            ["Front", "Back", "Phone", "Url", "Title", "Cover"],
        )
        self.assertEqual(
            self._sticky(m),
            {"Front": True, "Back": True, "Phone": False, "Url": True, "Title": True, "Cover": False},
        )
        self.assertEqual(m["sortf"], 0)  # Front
        self.assertEqual(m["css"], _PROD_CSS_EXTRACT)
        t = m["tmpls"][0]
        self.assertEqual(
            t["qfmt"], _PROD_HEADER + "{{Front}}\n<br>\n{{tts en_US :Back}}\n\n" + _PROD_COVER
        )
        self.assertEqual(
            t["afmt"], "{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}\n\n<p>{{Phone}}</p>"
        )
        self.assertEqual(t["bqfmt"], "{{Front}}")

    def test_speak_parity(self):
        m = self._build("LSA-Speak")
        self.assertEqual(
            [f["name"] for f in m["flds"]],
            ["Front", "Back", "Phone", "Url", "Title", "Cover"],
        )
        t = m["tmpls"][0]
        self.assertEqual(t["qfmt"], _PROD_HEADER + "{{Front}}\n\n" + _PROD_COVER)
        self.assertEqual(
            t["afmt"], "{{FrontSide}}\n\n<hr id=answer>\n\n{{tts en_US :Back}}\n\n<p>{{Phone}}</p>"
        )
        self.assertEqual(t["bqfmt"], "{{Front}}")
        self.assertEqual(m["css"], _PROD_CSS_EXTRACT)


if __name__ == "__main__":
    unittest.main()
