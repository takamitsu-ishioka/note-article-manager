#!/usr/bin/env python3
"""Apply lossless, deterministic ChatGPT-export cleanup for a note article."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SPEAKER_HEADINGS = {"## Prompt:": "## 私：", "## Response:": "## ChatGPT:"}
EXPORT_METADATA_RE = re.compile(r"^\*\*(?:Created|Updated|Exported):\*\*.*$")
LINK_METADATA_RE = re.compile(r"^\*\*Link:\*\*.*$")
SPEAKER_TIMESTAMP_RE = re.compile(
    r"^\d{4}/\d{1,2}/\d{1,2}\s+\d{1,2}:\d{2}:\d{2}(?:\s+·\s+.+)?\s*$"
)
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ESCAPED_HASH_RE = re.compile(r"^\\#")
ESCAPED_NUMBER_RE = re.compile(r"\\\.")
HTML_QUOTE_RE = re.compile(r"^&gt;\s?(.*)$")


def normalize_content_line(line: str) -> str:
    """Make exporter escaping explicit and retain note-compatible inline HTML."""
    if quote := HTML_QUOTE_RE.fullmatch(line):
        line = f"<blockquote>{quote.group(1)}</blockquote>"
    line = ESCAPED_HASH_RE.sub("#", line)
    line = ESCAPED_NUMBER_RE.sub(".", line)
    return BOLD_RE.sub(r"<strong>\1</strong>", line)


def prepare(markdown: str) -> str:
    """Remove exporter-only timestamps and normalize exporter speaker headings."""
    result: list[str] = []
    discard_next_timestamp = False
    for raw_line in markdown.splitlines():
        line = raw_line.rstrip(" \u200b")
        if EXPORT_METADATA_RE.fullmatch(line) or LINK_METADATA_RE.fullmatch(line):
            continue
        if discard_next_timestamp and SPEAKER_TIMESTAMP_RE.fullmatch(line):
            discard_next_timestamp = False
            continue
        if line in SPEAKER_HEADINGS:
            result.append(SPEAKER_HEADINGS[line])
            discard_next_timestamp = True
            continue
        if line:
            discard_next_timestamp = False
        result.append(normalize_content_line(line))
    return "\n".join(result).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="ChatGPT Exporter原稿の決定論的なnote前処理")
    parser.add_argument("source", type=Path, help="未加工の source.md")
    parser.add_argument("output", type=Path, help="整形後の article.md")
    args = parser.parse_args()
    if not args.source.is_file():
        print(f"error: source が見つかりません: {args.source}", file=sys.stderr)
        return 2
    try:
        source = args.source.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"error: UTF-8 として読めません: {args.source}", file=sys.stderr)
        return 2
    prepared = prepare(source)
    if not prepared.startswith("# "):
        print("error: 先頭に H1 タイトルがありません。", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(prepared, encoding="utf-8", newline="\n")
    print(f"整形しました: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
