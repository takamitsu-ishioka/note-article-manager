#!/usr/bin/env python3
"""Render $$...$$ TeX blocks as PNG assets for note articles."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "tools" / "render_tex_formula.js"
DISPLAY_MATH_RE = re.compile(r"^\$\$\s*$\n(.*?)^\$\$\s*$", re.MULTILINE | re.DOTALL)


def formula_blocks(markdown: str) -> list[tuple[tuple[int, int], str]]:
    return [((match.start(), match.end()), match.group(1).strip()) for match in DISPLAY_MATH_RE.finditer(markdown)]


def convert(article: Path) -> int:
    markdown = article.read_text(encoding="utf-8")
    blocks = formula_blocks(markdown)
    if not blocks:
        return 0
    replacements: list[tuple[tuple[int, int], str]] = []
    for number, (span, formula) in enumerate(blocks, start=1):
        tex_path = article.parent / f"formula{number}.tex"
        svg_path = article.parent / f"formula{number}.svg"
        png_path = article.parent / f"formula{number}.png"
        if any(path.exists() for path in (tex_path, svg_path, png_path)):
            raise ValueError(f"既存の数式画像を上書きしません: formula{number}")
        tex_path.write_text(formula + "\n", encoding="utf-8", newline="\n")
        try:
            subprocess.run(["node", str(RENDERER), str(tex_path), str(svg_path)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            subprocess.run(
                ["convert", "-background", "white", str(svg_path), "-resize", "952x952>", "-bordercolor", "white", "-border", "24", str(png_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except FileNotFoundError as exc:
            raise ValueError("node または ImageMagick の convert コマンドが見つかりません。") from exc
        except subprocess.CalledProcessError as exc:
            png_path.unlink(missing_ok=True)
            raise ValueError(f"formula{number} のレンダリングに失敗しました: {exc.stderr.strip()}") from exc
        replacements.append((span, f"TODO: formula{number}.png"))
    result: list[str] = []
    position = 0
    for (start, end), replacement in replacements:
        result.append(markdown[position:start])
        result.append(replacement)
        position = end
    result.append(markdown[position:])
    article.write_text("".join(result), encoding="utf-8", newline="\n")
    return len(blocks)


def main() -> int:
    parser = argparse.ArgumentParser(description="$$...$$ TeX数式をformulaN.pngへ変換し、本文をTODO参照に置換する")
    parser.add_argument("article", type=Path)
    args = parser.parse_args()
    if not args.article.is_file():
        parser.error(f"article.md が見つかりません: {args.article}")
    try:
        count = convert(args.article)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"TeX数式を {count} 件変換しました: {args.article}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
