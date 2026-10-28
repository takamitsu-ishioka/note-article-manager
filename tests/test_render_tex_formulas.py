import importlib.util
from pathlib import Path
import sys
import unittest


SCRIPT = Path(__file__).parents[1] / "tools" / "render_tex_formulas.py"
SPEC = importlib.util.spec_from_file_location("render_tex_formulas", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class RenderTexFormulasTest(unittest.TestCase):
    def test_finds_display_math_blocks(self):
        blocks = MODULE.formula_blocks("前文\n$$\n\\frac{dH_i}{dt}\n$$\n後文\n")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0][1], r"\frac{dH_i}{dt}")


if __name__ == "__main__":
    unittest.main()
