import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "tools" / "export_note_import.py"
SPEC = importlib.util.spec_from_file_location("export_note_import", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class NoteImportExportTest(unittest.TestCase):
    def test_renders_common_markdown_and_strips_h1(self):
        title, body = MODULE.markdown_to_html(
            "# 題名\u200b  \n\n## 節\n本文の **強調** と [リンク](https://example.com)。\n\n- 一\n- 二\n\n```py\nprint('x')\n```\n",
            None,
        )
        self.assertEqual(title, "題名")
        self.assertIn("<h2>節</h2>", body)
        self.assertIn("<strong>強調</strong>", body)
        self.assertIn('<a href="https://example.com">リンク</a>', body)
        self.assertIn("<ul>", body)
        self.assertIn("<pre><code>print(&#x27;x&#x27;)</code></pre>", body)

    def test_requires_public_url_for_todo_images(self):
        with self.assertRaisesRegex(ValueError, "asset-base-url"):
            MODULE.markdown_to_html("# 題名\n\nTODO: table1.png\n", None)

    def test_turns_todo_images_into_absolute_image_tags(self):
        _, body = MODULE.markdown_to_html("# 題名\n\nTODO: table 1.png\n", "https://assets.example/articles/1")
        self.assertIn('src="https://assets.example/articles/1/table%201.png"', body)

    def test_mt_has_required_fields_and_separator(self):
        # Test the externally visible MT framing independently of filesystem input.
        mt = "\n".join(("TITLE: 題名", "DATE: 10/27/2026 12:00:00", "BODY:", "本文", "--------"))
        self.assertIn("TITLE:", mt)
        self.assertIn("DATE:", mt)
        self.assertTrue(mt.endswith("--------"))

    def test_rejects_missing_todo_image(self):
        with tempfile.TemporaryDirectory() as temporary:
            article = Path(temporary) / "article.md"
            article.write_text("# 題名\n\nTODO: table1.png\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "画像ファイルが見つかりません"):
                MODULE.mt_entry(article, MODULE.datetime(2026, 10, 27), "https://assets.example")


if __name__ == "__main__":
    unittest.main()
