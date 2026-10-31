"""Unit tests for article_actions (change: add-article-row-actions).

Covers the four lifecycle handlers (spec: article-management):
add (empty prefill, declined gate), duplicate (copy prefill, progress
cleared, source untouched), edit (reviewer.card seam + restore), delete
(confirm / decline). Zero-dependency style like the rest of tests/: the
package is imported FIRST (its init() skips Anki hook registration when
aqt is absent), then a minimal aqt stub is installed for the lazy
`from aqt import dialogs` / `from aqt.qt import QMessageBox` imports.

NOTE: this file runs alphabetically BEFORE tests/test_hub.py, whose stub
installer returns early when `aqt` is already in sys.modules — so the
stub installed here must cover everything hub.py imports at module level
(QMainWindow, Qt.WindowType).
"""

import sys
import types
import unittest

import language_study_anki  # noqa: F401  (init() must run before the stub)
from language_study_anki import article_actions
from language_study_anki.provisioning import ARTICLE_FIELDS, ARTICLE_NOTE_TYPE

# ------------------------------------------------------------ aqt stub


class FakeDialogs:
    """Stub for aqt.dialogs: records open() calls, returns a prepared
    dialog; can be told to raise (design D2 seam-restore scenario)."""

    def __init__(self):
        self.calls = []
        self.dialog = None
        self.raise_exc = None
        self.record_card_at_open = None  # (mw) -> value, for seam checks

    def open(self, name, parent):
        if self.raise_exc is not None:
            raise self.raise_exc
        self.calls.append((name, parent))
        if self.record_card_at_open is not None:
            self.dialog.seen_card = self.record_card_at_open(parent)
        return self.dialog


class FakeAddDialog:
    def __init__(self):
        self.note = None
        self.deck_id = "<unset>"

    def set_note(self, note, deck_id=None):
        self.note = note
        self.deck_id = deck_id


class FakeMessageBox:
    class StandardButton:
        Yes = 1
        No = 2

    answer = StandardButton.No
    questions = []

    @classmethod
    def question(cls, parent, title, text, buttons, default):
        cls.questions.append((title, text))
        return cls.answer


def _install_aqt_stub() -> FakeDialogs:
    aqt = sys.modules.get("aqt")
    if aqt is None:
        aqt = types.ModuleType("aqt")
        sys.modules["aqt"] = aqt
    qt = getattr(aqt, "qt", None)
    if qt is None:
        qt = types.ModuleType("aqt.qt")
        aqt.qt = qt
        sys.modules["aqt.qt"] = qt
    if not hasattr(qt, "QMainWindow"):
        qt.QMainWindow = type("QMainWindow", (), {})
    if not hasattr(qt, "Qt"):

        class _WindowType:
            Window = 0x00000001
            WindowMinimizeButtonHint = 0x10000000
            WindowMaximizeButtonHint = 0x02000000

        qt.Qt = types.SimpleNamespace(WindowType=_WindowType)
    qt.QMessageBox = FakeMessageBox
    dialogs = FakeDialogs()
    aqt.dialogs = dialogs
    return dialogs


DIALOGS = _install_aqt_stub()


# ------------------------------------------------------------- fakes


class FakeNote:
    def __init__(self, nid=0, note_type_name=ARTICLE_NOTE_TYPE,
                 field_names=None, **fields):
        self.id = nid
        self.fields = dict(fields)
        self._nt_name = note_type_name
        self._names = set(
            field_names if field_names is not None else ARTICLE_FIELDS
        )

    def __getitem__(self, key):
        return self.fields[key]  # KeyError for absent fields, like a Note

    def __setitem__(self, key, value):
        if key not in self._names:
            raise KeyError(key)  # foreign types may lack our fields
        self.fields[key] = value

    def note_type(self):
        return {"name": self._nt_name}


class FakeModels:
    def __init__(self, article_type_present=True):
        self.present = article_type_present

    def by_name(self, name):
        if name == ARTICLE_NOTE_TYPE and self.present:
            return {"id": 1, "name": ARTICLE_NOTE_TYPE}
        return None


class FakeCol:
    def __init__(self, notes=None, article_type_present=True):
        self.notes = dict(notes or {})
        self.models = FakeModels(article_type_present)
        self.removed = []
        self.new_note_calls = []

    def get_note(self, nid):
        return self.notes[nid]  # KeyError for unknown ids, like a real col

    def new_note(self, model):
        self.new_note_calls.append(model)
        return FakeNote(nid=0, **{name: "" for name in ARTICLE_FIELDS})

    def current_deck_id(self):
        return 42

    def card_ids_of_note(self, nid):
        return [1000 + nid]

    def get_card(self, cid):
        return ("card", cid)

    def remove_notes(self, note_ids):
        self.removed.append(list(note_ids))


class FakeReviewer:
    def __init__(self, card=None):
        self.card = card


def _mw(col, card=None):
    return types.SimpleNamespace(col=col, reviewer=FakeReviewer(card))


def _source_note(**fields):
    values = {name: "" for name in ARTICLE_FIELDS}
    values.update(fields)
    return FakeNote(nid=7, **values)


# ------------------------------------------------------------- tests


class AddArticleTests(unittest.TestCase):
    def setUp(self):
        DIALOGS.calls = []
        DIALOGS.dialog = FakeAddDialog()
        DIALOGS.raise_exc = None
        FakeMessageBox.questions = []
        FakeMessageBox.answer = FakeMessageBox.StandardButton.No

    def test_add_opens_dialog_with_empty_note(self):
        col = FakeCol()
        dlg = article_actions.add_article(_mw(col), None)
        self.assertIs(dlg, DIALOGS.dialog)
        self.assertEqual([c[0] for c in DIALOGS.calls], ["AddCards"])
        note = dlg.note
        for name in ARTICLE_FIELDS:
            self.assertEqual(note[name], "", name)
        self.assertEqual(dlg.deck_id, col.current_deck_id())

    def test_add_declined_provisioning_gate_opens_nothing(self):
        # LSA-Article missing -> confirmation offered -> declined -> the
        # action is cancelled: no dialog, no note (spec: article-management
        # -> Actions require the article note type).
        FakeMessageBox.answer = FakeMessageBox.StandardButton.No
        col = FakeCol(article_type_present=False)
        self.assertIsNone(article_actions.add_article(_mw(col), None))
        self.assertEqual(DIALOGS.calls, [])
        self.assertEqual(col.new_note_calls, [])


class DuplicateArticleTests(unittest.TestCase):
    def setUp(self):
        DIALOGS.calls = []
        DIALOGS.dialog = FakeAddDialog()
        DIALOGS.raise_exc = None
        FakeMessageBox.questions = []
        FakeMessageBox.answer = FakeMessageBox.StandardButton.No

    def test_duplicate_prefills_copy_fields_with_fresh_progress(self):
        source = _source_note(
            Title="X",
            Content="Alpha<br>Beta",
            Translation="甲<br>乙",
            Url="https://example.com/a",
            Cover='<img src="cover.jpg">',
            ProgListening="3",
            ProgSpeaking="2",
            ProgReading="1",
            ProgWriting="3",
        )
        before = dict(source.fields)
        col = FakeCol(notes={7: source})

        dlg = article_actions.duplicate_article(_mw(col), None, 7)
        self.assertIs(dlg, DIALOGS.dialog)
        note = dlg.note
        self.assertEqual(note["Title"], "X (Copy)")
        self.assertEqual(note["Content"], "Alpha<br>Beta")
        self.assertEqual(note["Translation"], "甲<br>乙")
        self.assertEqual(note["Url"], "https://example.com/a")
        self.assertEqual(note["Cover"], '<img src="cover.jpg">')
        for name in article_actions.PROGRESS_FIELDS.values():
            self.assertEqual(note[name], "", name)
        # source untouched
        self.assertEqual(source.fields, before)
        self.assertEqual(dlg.deck_id, col.current_deck_id())

    def test_duplicate_rejects_non_article_note(self):
        source = FakeNote(nid=7, note_type_name="Basic", **{"Title": "X"})
        col = FakeCol(notes={7: source})
        with self.assertRaises(ValueError):
            article_actions.duplicate_article(_mw(col), None, 7)
        self.assertEqual(DIALOGS.calls, [])

    def test_duplicate_unknown_id_is_rejected(self):
        col = FakeCol(notes={})
        with self.assertRaises(KeyError):
            article_actions.duplicate_article(_mw(col), None, 99)


class EditArticleTests(unittest.TestCase):
    def setUp(self):
        DIALOGS.calls = []
        DIALOGS.dialog = FakeAddDialog()
        DIALOGS.raise_exc = None
        DIALOGS.record_card_at_open = None

    def test_edit_opens_under_seam_and_restores_previous_card(self):
        source = _source_note(Title="X")
        col = FakeCol(notes={7: source})
        mw = _mw(col, card="previous-card")
        seen = {}

        def record(parent):
            seen["card"] = parent.reviewer.card
            return parent.reviewer.card

        DIALOGS.record_card_at_open = record
        dlg = article_actions.edit_article(mw, None, 7)
        self.assertIs(dlg, DIALOGS.dialog)
        self.assertEqual([c[0] for c in DIALOGS.calls], ["EditCurrent"])
        # the dialog sees the article's card while it reads its note...
        self.assertEqual(seen["card"], ("card", 1007))
        # ...and the previous card is restored afterwards
        self.assertEqual(mw.reviewer.card, "previous-card")

    def test_edit_restores_seam_when_open_raises(self):
        source = _source_note(Title="X")
        col = FakeCol(notes={7: source})
        mw = _mw(col, card="previous-card")
        DIALOGS.raise_exc = RuntimeError("boom")
        with self.assertRaises(RuntimeError):
            article_actions.edit_article(mw, None, 7)
        self.assertEqual(mw.reviewer.card, "previous-card")

    def test_edit_rejects_non_article_note(self):
        source = FakeNote(nid=7, note_type_name="Basic", **{"Title": "X"})
        col = FakeCol(notes={7: source})
        mw = _mw(col, card="previous-card")
        with self.assertRaises(ValueError):
            article_actions.edit_article(mw, None, 7)
        self.assertEqual(DIALOGS.calls, [])
        self.assertEqual(mw.reviewer.card, "previous-card")


class DeleteArticleTests(unittest.TestCase):
    def setUp(self):
        FakeMessageBox.questions = []

    def test_delete_after_confirmation_removes_note(self):
        source = _source_note(Title="Doomed")
        col = FakeCol(notes={7: source})
        FakeMessageBox.answer = FakeMessageBox.StandardButton.Yes
        self.assertTrue(article_actions.delete_article(_mw(col), None, 7))
        self.assertEqual(col.removed, [[7]])
        self.assertEqual(len(FakeMessageBox.questions), 1)
        self.assertIn("Doomed", FakeMessageBox.questions[0][1])

    def test_delete_declined_removes_nothing(self):
        source = _source_note(Title="Spared")
        col = FakeCol(notes={7: source})
        FakeMessageBox.answer = FakeMessageBox.StandardButton.No
        self.assertFalse(article_actions.delete_article(_mw(col), None, 7))
        self.assertEqual(col.removed, [])

    def test_delete_rejects_non_article_note(self):
        source = FakeNote(nid=7, note_type_name="Basic", **{"Title": "X"})
        col = FakeCol(notes={7: source})
        with self.assertRaises(ValueError):
            article_actions.delete_article(_mw(col), None, 7)
        self.assertEqual(FakeMessageBox.questions, [])
        self.assertEqual(col.removed, [])


if __name__ == "__main__":
    unittest.main()
