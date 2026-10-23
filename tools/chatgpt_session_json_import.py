#!/usr/bin/env python3
"""Import a ChatGPT Exporter JSON conversation into a new article directory."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


def as_text(value: object) -> str:
    return value if isinstance(value, str) else ""


def fence_svgs(text: str) -> str:
    """Keep inline SVG payloads intact until the note conversion step rasterizes them."""
    return re.sub(r"(<svg\b.*?</svg>)", r"```svg\n\1\n```", text, flags=re.DOTALL)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy a ChatGPT Exporter JSON source and generate an editable Markdown article."
    )
    parser.add_argument("source_file", type=Path)
    parser.add_argument("article_number", type=int)
    parser.add_argument("article_title")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.source_file.is_file():
        parser.error(f"source file not found: {args.source_file}")
    try:
        data = json.loads(args.source_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        parser.error(f"invalid JSON: {exc}")
    if not isinstance(data, dict) or not isinstance(data.get("messages"), list):
        parser.error("expected an object with a messages array")

    repo_root = Path(__file__).resolve().parent.parent
    dest = repo_root / "articles" / f"{args.article_number:03d}_{args.article_title}"
    backup = dest / "backup" / "source.json"
    article = dest / "article.md"
    if dest.exists():
        parser.error(f"destination already exists, refusing to overwrite: {dest}")

    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    dates = metadata.get("dates") if isinstance(metadata.get("dates"), dict) else {}
    user = metadata.get("user") if isinstance(metadata.get("user"), dict) else {}
    user_label = as_text(user.get("email")) or as_text(user.get("name"))
    lines = [f"# {args.article_title}", ""]
    if user_label:
        lines.extend([f"**User:** {user_label}", ""])
    for key in ("created", "updated", "exported"):
        value = as_text(dates.get(key))
        if value:
            lines.extend([f"**{key.title()}:** {value}", ""])

    svg_count = 0
    for message in data["messages"]:
        if not isinstance(message, dict):
            continue
        role = as_text(message.get("role"))
        if role not in {"Prompt", "Response"}:
            continue
        lines.extend([f"## {role}:", as_text(message.get("time")), ""])
        say = as_text(message.get("say"))
        svg_count += len(re.findall(r"<svg\b.*?</svg>", say, flags=re.DOTALL))
        lines.extend([fence_svgs(say), ""])

    powered_by = as_text(metadata.get("powered_by"))
    if powered_by:
        lines.extend(["---", powered_by, ""])
    output = "\n".join(lines).rstrip() + "\n"

    print(f"source: {args.source_file}")
    print(f"backup: {backup}")
    print(f"article: {article}")
    print(f"messages: {sum(1 for m in data['messages'] if isinstance(m, dict))}")
    print(f"inline SVGs: {svg_count}")
    if args.dry_run:
        return 0

    dest.mkdir(parents=True)
    backup.parent.mkdir()
    shutil.copy2(args.source_file, backup)
    article.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
