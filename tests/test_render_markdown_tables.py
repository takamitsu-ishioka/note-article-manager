import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "tools" / "render_markdown_tables.py"
SPEC = importlib.util.spec_from_file_location("render_markdown_tables", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class RenderMarkdownTablesTest(unittest.TestCase):
    def test_renders_and_replaces_a_table(self):
        with tempfile.TemporaryDirectory() as temporary:
            article = Path(temporary) / "article.md"
            article.write_text("前文\n\n| A | B |\n|---|---|\n| 一 | 二 |\n\n後文\n", encoding="utf-8")
            self.assertEqual(MODULE.convert(article), 1)
            self.assertIn("TODO: table1.png", article.read_text(encoding="utf-8"))
            image = article.parent / "table1.png"
            self.assertTrue(image.is_file())
            self.assertEqual(MODULE.Image.open(image).getpixel((0, 0)), (52, 58, 64))

    def test_interprets_strong_tags_as_bold_text_not_literals(self):
        self.assertEqual(
            MODULE.cell_segments("<strong>合計</strong>：<strong>100</strong>"),
            [("合計", True), ("：", False), ("100", True)],
        )


if __name__ == "__main__":
    unittest.main()
