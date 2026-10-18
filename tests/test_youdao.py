import io
import json
import os
import tempfile
import unittest
import urllib.error
from unittest import mock

from language_study_anki import youdao
from language_study_anki.youdao import DictEntry, LookupResult, format_phonetics, lookup


class FakeResponse:
    def __init__(self, payload: bytes, status: int = 200):
        self._payload = payload
        self.status = status

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


EXPAND_EC = {
    "expand_ec": {
        "word": [
            {
                "pos": "adj.",
                "transList": [{"trans": "短暂的"}, {"trans": "短暂"}],
            },
            {"pos": "n.", "transList": [{"trans": "片刻"}]},
        ]
    }
}

EC_FALLBACK = {
    "ec": {
        "word": [
            {
                "trs": [
                    {"tr": [{"l": {"i": ["adj. 短暂的；短命的"]}}]},
                    {"tr": [{"l": {"i": ["n. 一时"]}}]},
                ]
            }
        ]
    }
}

EC_NO_POS = {"ec": {"word": [{"trs": [{"tr": [{"l": {"i": ["永恒"]}}]}]}]}}


def patch_response(payload, status=200):
    body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    return mock.patch.object(
        youdao.urllib.request, "urlopen", return_value=FakeResponse(body, status)
    )


class ParseTests(unittest.TestCase):
    def test_expand_ec_parsed(self):
        with patch_response(EXPAND_EC):
            entries = list(lookup("ephemeral").entries)
        self.assertEqual(
            entries,
            [
                DictEntry(pos="adj.", tran="短暂的；短暂"),
                DictEntry(pos="n.", tran="片刻"),
            ],
        )

    def test_ec_fallback_parsed(self):
        with patch_response(EC_FALLBACK):
            entries = list(lookup("eternal").entries)
        self.assertEqual(
            entries,
            [
                DictEntry(pos="adj. ", tran="短暂的；短命的"),
                DictEntry(pos="n. ", tran="一时"),
            ],
        )

    def test_ec_without_pos_keeps_full_text(self):
        with patch_response(EC_NO_POS):
            entries = list(lookup("foo").entries)
        self.assertEqual(entries, [DictEntry(pos="", tran="永恒")])


class FailureTests(unittest.TestCase):
    def test_unknown_word_empty_result(self):
        with patch_response({}):
            self.assertEqual(lookup("nonexistentword"), LookupResult((), ()))

    def test_network_failure_returns_empty(self):
        with mock.patch.object(
            youdao.urllib.request,
            "urlopen",
            side_effect=urllib.error.URLError("down"),
        ):
            self.assertEqual(lookup("ephemeral"), LookupResult((), ()))

    def test_timeout_returns_empty(self):
        with mock.patch.object(
            youdao.urllib.request, "urlopen", side_effect=TimeoutError
        ):
            self.assertEqual(lookup("ephemeral"), LookupResult((), ()))

    def test_malformed_json_returns_empty(self):
        with patch_response(b"not json{"):
            self.assertEqual(lookup("ephemeral"), LookupResult((), ()))

    def test_non_200_returns_empty(self):
        with patch_response(EXPAND_EC, status=500):
            self.assertEqual(lookup("ephemeral"), LookupResult((), ()))

    def test_empty_word_makes_no_request(self):
        with mock.patch.object(youdao.urllib.request, "urlopen") as m:
            self.assertEqual(lookup("   "), LookupResult((), ()))
            m.assert_not_called()


if __name__ == "__main__":
    unittest.main()

PHONE_JSON = {"simple": {"word": [{"ukphone": "ɪˈfemərəl", "usphone": "ɪˈfemərəl"}]}}
EC_PHONE_JSON = {"ec": {"word": [{"ukphone": "ɪˈfemərəl", "usphone": "ɪˈfemərəl"}]}}


class PhoneticsTests(unittest.TestCase):
    def test_phonetics_from_simple(self):
        with patch_response(PHONE_JSON):
            res = lookup("ephemeral")
        w0 = PHONE_JSON["simple"]["word"][0]
        self.assertEqual(
            res.phonetics,
            (("UK", w0["ukphone"]), ("US", w0["usphone"])),
        )

    def test_phonetics_fallback_to_ec(self):
        with patch_response(EC_PHONE_JSON):
            res = lookup("ephemeral")
        self.assertEqual([r for r, _ in res.phonetics], ["UK", "US"])

    def test_format_phonetics_flutter_parity(self):
        s = format_phonetics([("UK", "a"), ("US", "b")])
        self.assertEqual(s, "UK /a/ US /b/")

    def test_no_phonetics_when_absent(self):
        with patch_response(EXPAND_EC):
            res = lookup("ephemeral")
        self.assertEqual(res.phonetics, ())


class DiagnosticsTests(unittest.TestCase):
    """Failures stay traceable: a log line + last_error, and never a raise."""

    def setUp(self):
        self.log_file = os.path.join(tempfile.mkdtemp(), "youdao.log")
        env = mock.patch.dict(os.environ, {"LSA_YOUDAO_LOG": self.log_file})
        env.start()
        self.addCleanup(env.stop)

    def _log_text(self):
        with open(self.log_file, encoding="utf-8") as fh:
            return fh.read()

    def test_success_not_logged_and_last_error_cleared(self):
        with patch_response(EXPAND_EC):
            res = lookup("ephemeral")
        self.assertTrue(res.entries)
        self.assertEqual(youdao.last_error, "")
        self.assertFalse(os.path.exists(self.log_file))  # success writes nothing

    def test_network_failure_logged_with_reason(self):
        with mock.patch.object(
            youdao.urllib.request,
            "urlopen",
            side_effect=urllib.error.URLError("down"),
        ):
            self.assertEqual(lookup("ephemeral"), LookupResult((), ()))
        self.assertIn("URLError", youdao.last_error)
        self.assertIn("FAIL URLError", self._log_text())

    def test_non_200_logged_with_status(self):
        with patch_response(EXPAND_EC, status=500):
            self.assertEqual(lookup("ephemeral"), LookupResult((), ()))
        self.assertEqual(youdao.last_error, "http 500")
        self.assertIn("FAIL http 500", self._log_text())

    def test_no_dict_fields_logged_with_response_keys(self):
        # dict.youdao.com answers full sentences without ec/expand_ec.
        with patch_response({"input": "whole line", "lang": "en"}):
            self.assertEqual(lookup("a whole sentence"), LookupResult((), ()))
        self.assertIn("no dictionary fields", youdao.last_error)
        self.assertIn("input", self._log_text())

    def test_unwritable_log_never_breaks_lookup(self):
        blocker = os.path.join(tempfile.mkdtemp(), "blocker")
        with open(blocker, "w", encoding="utf-8") as fh:
            fh.write("not a directory")
        bad_path = os.path.join(blocker, "sub", "youdao.log")  # parent is a file
        with mock.patch.dict(os.environ, {"LSA_YOUDAO_LOG": bad_path}):
            with patch_response({"input": "x"}):  # empty outcome → records
                res = lookup("hello")
        # _record failed internally, but the lookup still completed normally
        self.assertEqual(res, LookupResult((), ()))
        self.assertIn("no dictionary fields", youdao.last_error)
        self.assertFalse(os.path.exists(bad_path))

    def test_empty_word_records_nothing(self):
        lookup("   ")
        self.assertFalse(os.path.exists(self.log_file))
