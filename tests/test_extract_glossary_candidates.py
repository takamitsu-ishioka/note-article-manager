import importlib.util
from pathlib import Path
import sys
import unittest


SCRIPT = Path(__file__).parents[1] / "tools" / "extract_glossary_candidates.py"
SPEC = importlib.util.spec_from_file_location("extract_glossary_candidates", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class VisibleLinesTest(unittest.TestCase):
    def test_omits_fenced_code_and_markdown_markup(self):
        markdown = "# 見出し\n本文の**API**です。\n```bash\ngrep secret\n```\n"
        self.assertEqual(
            list(MODULE.visible_lines(markdown)),
            [(1, "見出し"), (2, "本文のAPIです。")],
        )


class CandidateTest(unittest.TestCase):
    def test_frequency_lookup_does_not_require_mecab(self):
        self.assertGreater(MODULE.direct_zipf_frequency("哲学"), 0)
        self.assertEqual(MODULE.direct_zipf_frequency("SSoT"), 0)
        self.assertGreater(MODULE.general_zipf_frequency("具体的", "japanese"), 0)

    def test_extracts_rare_acronym_deterministically(self):
        markdown = "SSoTを利用する。\nSSoTは情報源である。\n"
        first = MODULE.build_candidates(markdown, limit=10, threshold=0)
        second = MODULE.build_candidates(markdown, limit=10, threshold=0)
        self.assertEqual(first, second)
        ssot = next(item for item in first if item["term"] == "SSoT")
        self.assertEqual(ssot["articleFrequency"], 2)
        self.assertIn("acronym", ssot["signals"])
        self.assertEqual(ssot["firstOccurrence"]["line"], 1)

    def test_preserves_adjacent_nouns_as_a_compound(self):
        candidates = MODULE.build_candidates("環境変数を設定する。", limit=20, threshold=0)
        compound = next(item for item in candidates if item["term"] == "環境変数")
        self.assertIn("compound_noun", compound["signals"])


if __name__ == "__main__":
    unittest.main()
