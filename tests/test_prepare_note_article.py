import importlib.util
from pathlib import Path
import sys
import unittest


SCRIPT = Path(__file__).parents[1] / "tools" / "prepare_note_article.py"
SPEC = importlib.util.spec_from_file_location("prepare_note_article", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class PrepareNoteArticleTest(unittest.TestCase):
    def test_removes_only_exporter_metadata_and_speaker_timestamps(self):
        source = """# 題名
**User:** Anonymous  
**Created:** 10/25/2026 6:58:39  
**Updated:** 10/25/2026 7:59:36

## Prompt:
2026/10/25 7:06:54

本文
## Response:
2026/10/25 7:06:59 · gpt-6

応答
"""
        self.assertEqual(
            MODULE.prepare(source),
            "# 題名\n<strong>User:</strong> Anonymous\n\n## 私：\n\n本文\n## ChatGPT:\n\n応答\n",
        )

    def test_keeps_a_regular_date_in_body(self):
        source = "# 題名\n\n2026/10/25 7:06:54 は公開日時ではない。\n"
        self.assertIn("2026/10/25", MODULE.prepare(source))

    def test_normalizes_exporter_escapes_and_removes_link_metadata(self):
        source = """# 題名
**Link:** [会話](https://example.com)

**強調**
\\#タグ
## 1\\. 節
&gt;引用 **強調**
"""
        self.assertEqual(
            MODULE.prepare(source),
            "# 題名\n\n<strong>強調</strong>\n#タグ\n## 1. 節\n<blockquote>引用 <strong>強調</strong></blockquote>\n",
        )


if __name__ == "__main__":
    unittest.main()
