#!/usr/bin/env python3
"""Render simple GitHub-flavored Markdown tables as deterministic PNG artifacts."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_SIZE = 28
CELL_PADDING_X = 22
CELL_PADDING_Y = 16
BORDER = 2


def cells(line: str) -> list[str]:
    parts = line.strip().strip("|").split("|")
    return [part.strip() for part in parts]


def table_blocks(lines: list[str]) -> list[tuple[int, int, list[list[str]]]]:
    blocks = []
    index = 0
    while index + 1 < len(lines):
        if "|" not in lines[index] or not TABLE_SEPARATOR_RE.match(lines[index + 1]):
            index += 1
            continue
        rows = [cells(lines[index])]
        end = index + 2
        while end < len(lines) and "|" in lines[end] and lines[end].strip():
            rows.append(cells(lines[end]))
            end += 1
        if len({len(row) for row in rows}) != 1:
            raise ValueError(f"{index + 1}行目の表は列数が一致しません。")
        blocks.append((index, end, rows))
        index = end
    return blocks


def render(rows: list[list[str]], output: Path) -> None:
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    column_widths = [max(probe.textbbox((0, 0), row[column], font=font)[2] for row in rows) + CELL_PADDING_X * 2 for column in range(len(rows[0]))]
    row_heights = [font.getbbox("あ")[3] - font.getbbox("あ")[1] + CELL_PADDING_Y * 2 for _ in rows]
    width = sum(column_widths) + BORDER * 2
    height = sum(row_heights) + BORDER * 2
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    y = 0
    for row_index, row in enumerate(rows):
        x = 0
        for column, value in enumerate(row):
            fill = "#f1f3f5" if row_index == 0 else "white"
            draw.rectangle((x, y, x + column_widths[column], y + row_heights[row_index]), fill=fill, outline="#343a40", width=BORDER)
            draw.text((x + CELL_PADDING_X, y + CELL_PADDING_Y), value, font=font, fill="#111827")
            x += column_widths[column]
        y += row_heights[row_index]
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, "PNG")


def convert(article: Path) -> int:
    lines = article.read_text(encoding="utf-8").splitlines()
    blocks = table_blocks(lines)
    if not blocks:
        return 0
    replacements: dict[tuple[int, int], str] = {}
    for number, (start, end, rows) in enumerate(blocks, start=1):
        output = article.parent / f"table{number}.png"
        if output.exists():
            raise ValueError(f"既存の表画像を上書きしません: {output}")
        render(rows, output)
        replacements[(start, end)] = f"TODO: table{number}.png"
    result: list[str] = []
    position = 0
    for (start, end), replacement in replacements.items():
        result.extend(lines[position:start])
        result.append(replacement)
        position = end
    result.extend(lines[position:])
    article.write_text("\n".join(result) + "\n", encoding="utf-8", newline="\n")
    return len(blocks)


def main() -> int:
    parser = argparse.ArgumentParser(description="Markdown表をtableN.pngへ変換し、本文をTODO参照に置換する")
    parser.add_argument("article", type=Path)
    args = parser.parse_args()
    if not args.article.is_file():
        parser.error(f"article.md が見つかりません: {args.article}")
    try:
        count = convert(args.article)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"表を {count} 件変換しました: {args.article}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
