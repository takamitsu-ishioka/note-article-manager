import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET


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
        self.assertIn('<a href="https://example.com" target="_blank">リンク</a>', body)
        self.assertIn("<ul>", body)
        self.assertIn("<pre><code>print(&#x27;x&#x27;)</code></pre>", body)

    def test_preserves_prepared_strong_and_blockquote_markup(self):
        _, body = MODULE.markdown_to_html(
            "# 題名\n\n<strong>強調</strong>\n\n<blockquote>引用 <strong>強調</strong></blockquote>\n",
            None,
        )
        self.assertIn("<p>\n    <strong>強調</strong><br>\n</p>", body)
        self.assertIn("<blockquote>引用 <strong>強調</strong></blockquote>", body)

    def test_renders_a_linked_markdown_image_as_an_img_tag(self):
        _, body = MODULE.markdown_to_html(
            "# 題名\n\n[![写真](https://images.example/photo?id=1)](https://source.example/article)\n",
            None,
        )
        self.assertIn(
            '<img src="https://images.example/photo?id=1" alt="写真">',
            body,
        )
        self.assertNotIn("source.example", body)

    def test_requires_public_url_for_todo_images(self):
        with self.assertRaisesRegex(ValueError, "asset-base-url"):
            MODULE.markdown_to_html("# 題名\n\nTODO: table1.png\n", None)

    def test_turns_todo_images_into_absolute_image_tags(self):
        _, body = MODULE.markdown_to_html("# 題名\n\nTODO: table 1.png\n", "https://assets.example/articles/1")
        self.assertIn('src="https://assets.example/articles/1/table%201.png"', body)

    def test_wxr_has_required_fields_and_is_valid_xml(self):
        with tempfile.TemporaryDirectory() as temporary:
            article = Path(temporary) / "article.md"
            article.write_text("# 題名\n\n本文\n", encoding="utf-8")
            item = MODULE.wxr_item(article, MODULE.datetime(2026, 10, 27), None)
        document = MODULE.wxr_document([item])
        root = ET.fromstring(document)
        content = root.find(".//{http://purl.org/rss/1.0/modules/content/}encoded")
        self.assertEqual(root.tag, "rss")
        self.assertIsNotNone(content)
        self.assertEqual(content.text, "<p>\n    本文<br>\n</p>")
        self.assertIn("<wp:status>publish</wp:status>", document)

    def test_html_preview_is_a_readable_document(self):
        preview = MODULE.html_preview("題名", "<p>本文</p>")
        self.assertIn("<title>題名</title>", preview)
        self.assertIn("<h1>題名</h1>", preview)
        self.assertIn("<p>本文</p>", preview)
        self.assertIn("        <p>本文</p>", preview)

    def test_turns_edited_html_into_wxr_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "article.html"
            source.write_text(MODULE.html_preview("編集後の題名", "<p>編集後の本文</p>"), encoding="utf-8")
            title, body = MODULE.editable_html_parts(source)
        document = MODULE.wxr_document([MODULE.wxr_item_from_html("310", title, body, MODULE.datetime(2026, 10, 27))])
        content = ET.fromstring(document).find(".//{http://purl.org/rss/1.0/modules/content/}encoded")
        self.assertEqual(title, "編集後の題名")
        self.assertEqual(content.text, "<p>編集後の本文</p>")

    def test_keeps_single_blank_separated_prose_in_one_compact_paragraph(self):
        _, body = MODULE.markdown_to_html(
            "# 題名\n\n一行目。\n\n二行目。\n\n\n別段落。\n",
            None,
        )
        self.assertIn("<p>\n    一行目。<br>\n    二行目。<br>\n</p>", body)
        self.assertIn("<p>\n    別段落。<br>\n</p>", body)

    def test_merges_empty_quote_lines_into_one_blockquote(self):
        _, body = MODULE.markdown_to_html(
            "# 題名\n\n> <strong>8件のウェブサイトを検索しました</strong>\n>\n> \n>\n> 6s考えました\n",
            None,
        )
        self.assertIn(
            "<p>\n<blockquote>\n<strong>8件のウェブサイトを検索しました</strong>\n<br>\n<br>\n<br>\n6s考えました\n</blockquote>\n</p>",
            body,
        )

    def test_rejects_missing_todo_image(self):
        with tempfile.TemporaryDirectory() as temporary:
            article = Path(temporary) / "article.md"
            article.write_text("# 題名\n\nTODO: table1.png\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "画像ファイルが見つかりません"):
                MODULE.wxr_item(article, MODULE.datetime(2026, 10, 27), "https://assets.example")


if __name__ == "__main__":
    unittest.main()
