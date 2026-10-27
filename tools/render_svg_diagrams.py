#!/usr/bin/env python3
"""Convert fenced SVG diagrams in an article into PNG assets for note import."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def convert(article: Path) -> int:
    lines = article.read_text(encoding="utf-8").splitlines()
    result: list[str] = []
    index = 0
    number = 0
    while index < len(lines):
        if lines[index].strip().lower() != "```svg":
            result.append(lines[index])
            index += 1
            continue
        end = index + 1
        while end < len(lines) and lines[end].strip() != "```":
            end += 1
        if end == len(lines):
            raise ValueError(f"{index + 1}行目のSVGコードブロックが閉じていません。")
        svg = "\n".join(lines[index + 1:end]).strip()
        if not svg.startswith("<svg") or not svg.endswith("</svg>"):
            raise ValueError(f"{index + 1}行目のSVGコードブロックがSVG要素ではありません。")
        number += 1
        svg_path = article.parent / f"figure{number}.svg"
        png_path = article.parent / f"figure{number}.png"
        if svg_path.exists() or png_path.exists():
            raise ValueError(f"既存の図を上書きしません: {svg_path.name} / {png_path.name}")
        svg_path.write_text(svg + "\n", encoding="utf-8", newline="\n")
        try:
            subprocess.run(
                ["convert", "-background", "white", str(svg_path), str(png_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except FileNotFoundError as exc:
            raise ValueError("ImageMagick の convert コマンドが見つかりません。") from exc
        except subprocess.CalledProcessError as exc:
            png_path.unlink(missing_ok=True)
            raise ValueError(f"{svg_path.name} のPNG変換に失敗しました: {exc.stderr.strip()}") from exc
        result.append(f"TODO: figure{number}.png")
        index = end + 1
    article.write_text("\n".join(result) + "\n", encoding="utf-8", newline="\n")
    return number


def main() -> int:
    parser = argparse.ArgumentParser(description="fenced SVG図をfigureN.pngへ変換し、本文をTODO参照に置換する")
    parser.add_argument("article", type=Path)
    args = parser.parse_args()
    if not args.article.is_file():
        parser.error(f"article.md が見つかりません: {args.article}")
    try:
        count = convert(args.article)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"SVG図を {count} 件変換しました: {args.article}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
