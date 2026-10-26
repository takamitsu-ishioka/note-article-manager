#!/usr/bin/env python3
"""Create a note-compatible Movable Type import file from article directories.

The resulting file is deliberately an import *package*, not a publishing API:
note imports every entry as a draft and the author reviews and publishes it there.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
DATE_RE = re.compile(r"^\s*\d+\. (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) — \[.*?\]\(<(articles/[^>]+/article\.md)>\)$")
TODO_IMAGE_RE = re.compile(r"^\s*TODO:\s*(.+\.(?:png|jpe?g|gif))\s*$", re.IGNORECASE)
INLINE_RE = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def article_date(article: Path) -> datetime:
    relative = article.resolve().relative_to(ROOT).as_posix()
    index = (ROOT / "index.md").read_text(encoding="utf-8")
    for line in index.splitlines():
        match = DATE_RE.match(line)
        if match and match.group(2) == relative:
            return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
    raise ValueError(f"index.md に {relative} の日時がありません。--date を指定してください。")


def image_url(asset_base_url: str, filename: str) -> str:
    return asset_base_url.rstrip("/") + "/" + quote(filename)


def validate_local_assets(article: Path, markdown: str) -> None:
    """Fail before export if a TODO or relative Markdown image has no source file."""
    filenames = [match.group(1) for line in markdown.splitlines() if (match := TODO_IMAGE_RE.match(line))]
    filenames.extend(match.group(3) for match in INLINE_RE.finditer(markdown) if match.group(1) and not re.match(r"https?://", match.group(3)))
    for filename in filenames:
        candidate = (article.parent / filename).resolve()
        try:
            candidate.relative_to(article.parent.resolve())
        except ValueError as exc:
            raise ValueError(f"画像パスは記事ディレクトリ外を参照できません: {filename}") from exc
        if not candidate.is_file():
            raise ValueError(f"画像ファイルが見つかりません: {candidate}")


def inline_html(text: str, asset_base_url: str | None) -> str:
    """Render the intentionally small Markdown subset used by article.md."""
    escaped = html.escape(text, quote=False)

    def replace_link(match: re.Match[str]) -> str:
        image, label, target = match.groups()
        target = html.unescape(target)
        if image:
            if not re.match(r"https?://", target):
                if not asset_base_url:
                    raise ValueError(f"ローカル画像 {target} には --asset-base-url が必要です。")
                target = image_url(asset_base_url, target)
            return f'<img src="{html.escape(target, quote=True)}" alt="{html.escape(label, quote=True)}">'
        return f'<a href="{html.escape(target, quote=True)}">{label}</a>'

    escaped = INLINE_RE.sub(replace_link, escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)
    return escaped.replace("\u200b", "")


def markdown_to_html(markdown: str, asset_base_url: str | None) -> tuple[str, str]:
    lines = markdown.splitlines()
    title = ""
    if lines and (match := re.match(r"^#\s+(.+?)\s*$", lines[0].replace("\u200b", ""))):
        title = match.group(1)
        lines = lines[1:]
    if not title:
        raise ValueError("article.md の先頭に H1 タイトルがありません。")

    output: list[str] = []
    paragraph: list[str] = []
    list_kind: str | None = None
    quote_lines: list[str] = []
    fenced = False
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            output.append("<p>" + "<br>".join(inline_html(x, asset_base_url) for x in paragraph) + "</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_kind
        if list_kind:
            output.append(f"</{list_kind}>")
            list_kind = None

    def flush_quote() -> None:
        nonlocal quote_lines
        if quote_lines:
            output.append("<blockquote><p>" + "<br>".join(inline_html(x, asset_base_url) for x in quote_lines) + "</p></blockquote>")
            quote_lines = []

    for raw_line in lines:
        line = raw_line.rstrip().replace("\u200b", "")
        if line.startswith("```"):
            flush_paragraph(); flush_list(); flush_quote()
            if fenced:
                output.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
                code_lines = []
            fenced = not fenced
            continue
        if fenced:
            code_lines.append(raw_line)
            continue
        todo = TODO_IMAGE_RE.match(line)
        if todo:
            flush_paragraph(); flush_list(); flush_quote()
            filename = todo.group(1)
            if not asset_base_url:
                raise ValueError(f"{filename} を取り込むには --asset-base-url が必要です。")
            output.append(f'<p><img src="{html.escape(image_url(asset_base_url, filename), quote=True)}" alt="{html.escape(filename, quote=True)}"></p>')
            continue
        if not line:
            flush_paragraph(); flush_list(); flush_quote()
            continue
        if line in {"---", "***", "___"}:
            flush_paragraph(); flush_list(); flush_quote(); output.append("<hr>"); continue
        if match := re.match(r"^(#{2,6})\s+(.+)$", line):
            flush_paragraph(); flush_list(); flush_quote()
            level = len(match.group(1))
            output.append(f"<h{level}>{inline_html(match.group(2), asset_base_url)}</h{level}>")
            continue
        if line.startswith("> "):
            flush_paragraph(); flush_list(); quote_lines.append(line[2:]); continue
        if match := re.match(r"^[-*+]\s+(.+)$", line):
            flush_paragraph(); flush_quote()
            if list_kind and list_kind != "ul": flush_list()
            if not list_kind: output.append("<ul>"); list_kind = "ul"
            output.append("<li>" + inline_html(match.group(1), asset_base_url) + "</li>")
            continue
        if match := re.match(r"^\d+[.)]\s+(.+)$", line):
            flush_paragraph(); flush_quote()
            if list_kind and list_kind != "ol": flush_list()
            if not list_kind: output.append("<ol>"); list_kind = "ol"
            output.append("<li>" + inline_html(match.group(1), asset_base_url) + "</li>")
            continue
        flush_list(); flush_quote(); paragraph.append(line)

    if fenced:
        raise ValueError("閉じていない fenced code block があります。")
    flush_paragraph(); flush_list(); flush_quote()
    return title, "\n".join(output)


def mt_entry(article: Path, date: datetime, asset_base_url: str | None) -> str:
    markdown = article.read_text(encoding="utf-8")
    validate_local_assets(article, markdown)
    title, body = markdown_to_html(markdown, asset_base_url)
    # A literal CDATA terminator can occur in a code sample. Split it safely.
    body = body.replace("]]>", "]]]]><![CDATA[>")
    # note accepts MT text as UTF-8 and requires TITLE, BODY, DATE and --------.
    return "\n".join((
        "AUTHOR: note-article-manager",
        f"TITLE: {title}",
        f"BASENAME: article-{article.parent.name.split('_', 1)[0]}",
        "STATUS: Publish",
        "ALLOW COMMENTS: 0",
        "CONVERT BREAKS: 0",
        f"DATE: {date.strftime('%m/%d/%Y %H:%M:%S')}",
        "-----",
        "BODY:",
        "<![CDATA[",
        body,
        "]]>",
        "--------",
        "",
    ))


def main() -> int:
    parser = argparse.ArgumentParser(description="note インポート用 MT ファイルを生成する")
    parser.add_argument("articles", nargs="+", type=Path, help="記事ディレクトリ、または article.md")
    parser.add_argument("-o", "--output", required=True, type=Path, help="出力する .txt ファイル")
    parser.add_argument("--asset-base-url", help="table1.png 等を公開している URL のベース")
    parser.add_argument("--date", help="単一記事時の日時上書き (YYYY-MM-DD HH:MM:SS)")
    args = parser.parse_args()
    if args.output.suffix.lower() != ".txt":
        parser.error("note の MT インポート用に出力ファイルは .txt にしてください。")
    if args.date and len(args.articles) != 1:
        parser.error("--date は単一記事のときだけ指定できます。")
    try:
        entries = []
        for target in args.articles:
            article = target if target.name == "article.md" else target / "article.md"
            if not article.is_file():
                raise ValueError(f"article.md が見つかりません: {article}")
            date = datetime.strptime(args.date, "%Y-%m-%d %H:%M:%S") if args.date else article_date(article)
            entries.append(mt_entry(article, date, args.asset_base_url))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(entries), encoding="utf-8", newline="\n")
    print(f"生成しました: {args.output} ({len(entries)} 件)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
