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
    build_confirm_message,
    missing_items,
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
        col = FakeCol(note_types=["@Basic"], decks=["English"])
        self.assertEqual(
            missing_items(col, "extract"),
            {"note_types": ["@EnListen", "@EnSpeak"], "decks": []},
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
            {"note_types": ["@Basic"], "decks": [EXTRACT_DECK]}
        )
        self.assertIn("Note types: @Basic", msg)
        self.assertIn(f"Decks: {EXTRACT_DECK}", msg)

    def test_article_scope_omits_deck_line(self):
        msg = build_confirm_message(
            {"note_types": [ARTICLE_NOTE_TYPE], "decks": []}
        )
        self.assertIn(ARTICLE_NOTE_TYPE, msg)
        self.assertNotIn("Decks:", msg)

    def test_lists_all_missing_types_in_order(self):
        msg = build_confirm_message(
            {"note_types": ["@Basic", "@EnListen", "@EnSpeak"], "decks": []}
        )
        self.assertIn("Note types: @Basic, @EnListen, @EnSpeak", msg)

    def test_never_lists_present_items(self):
        # Only the (already filtered) missing dict is rendered.
        msg = build_confirm_message({"note_types": ["@EnSpeak"], "decks": []})
        self.assertNotIn("@Basic", msg)
        self.assertNotIn("@EnListen", msg)

    def test_empty_missing_renders_empty_string(self):
        self.assertEqual(build_confirm_message({"note_types": [], "decks": []}), "")


if __name__ == "__main__":
    unittest.main()
