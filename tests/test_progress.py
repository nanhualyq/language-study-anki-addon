import unittest

from language_study_anki.progress import (
    PROGRESS_FIELDS,
    get_progress,
    progress_field,
    set_progress_at_least,
)


class FakeNote:
    """Minimal stand-in for anki.notes.Note (mapping + flush counter)."""

    def __init__(self, **fields):
        self.fields = dict(fields)
        self.flushes = 0

    def __getitem__(self, key):
        return self.fields[key]

    def __setitem__(self, key, value):
        self.fields[key] = value

    def flush(self):
        self.flushes += 1


class ReadTests(unittest.TestCase):
    def test_missing_field_defaults_to_zero(self):
        self.assertEqual(get_progress(FakeNote(), "reading"), 0)

    def test_valid_value_parsed(self):
        note = FakeNote(ProgReading="42")
        self.assertEqual(get_progress(note, "reading"), 42)

    def test_garbage_defaults_to_zero(self):
        note = FakeNote(ProgReading="abc")
        self.assertEqual(get_progress(note, "reading"), 0)

    def test_negative_clamped_to_zero(self):
        note = FakeNote(ProgReading="-3")
        self.assertEqual(get_progress(note, "reading"), 0)

    def test_field_mapping(self):
        self.assertEqual(progress_field("listening"), "ProgListening")
        self.assertEqual(PROGRESS_FIELDS["writing"], "ProgWriting")
        with self.assertRaises(KeyError):
            progress_field("unknown")


class WriteTests(unittest.TestCase):
    def test_extract_advances_field(self):
        note = FakeNote(ProgReading="0")
        changed = set_progress_at_least(note, "reading", 17)
        self.assertTrue(changed)
        self.assertEqual(note["ProgReading"], "17")
        self.assertEqual(note.flushes, 1)

    def test_extract_below_stored_value_does_not_decrease(self):
        note = FakeNote(ProgReading="42")
        changed = set_progress_at_least(note, "reading", 10)
        self.assertFalse(changed)
        self.assertEqual(note["ProgReading"], "42")
        self.assertEqual(note.flushes, 0)

    def test_equal_value_does_not_write(self):
        note = FakeNote(ProgReading="42")
        self.assertFalse(set_progress_at_least(note, "reading", 42))
        self.assertEqual(note.flushes, 0)

    def test_other_skills_untouched(self):
        note = FakeNote(ProgReading="0", ProgListening="5")
        set_progress_at_least(note, "reading", 9)
        self.assertEqual(note["ProgListening"], "5")

    def test_zero_or_negative_never_writes(self):
        note = FakeNote(ProgReading="0")
        self.assertFalse(set_progress_at_least(note, "reading", 0))
        self.assertFalse(set_progress_at_least(note, "reading", -1))
        self.assertEqual(note.flushes, 0)

    def test_no_flush_option(self):
        note = FakeNote(ProgReading="0")
        set_progress_at_least(note, "reading", 3, flush=False)
        self.assertEqual(note["ProgReading"], "3")
        self.assertEqual(note.flushes, 0)


if __name__ == "__main__":
    unittest.main()
