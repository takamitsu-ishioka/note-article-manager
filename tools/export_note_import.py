#!/usr/bin/env python3
"""Create a note-compatible WXR (WordPress XML) import file from article directories.

The resulting file is deliberately an import *package*, not a publishing API:
note imports every entry as a draft and the author reviews and publishes it there.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
DATE_RE = re.compile(r"^\s*\d+\. (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) — \[.*?\]\(<(articles/[^>]+/article\.md)>\)$")
TODO_IMAGE_RE = re.compile(r"^\s*TODO:\s*(.+\.(?:png|jpe?g|gif))\s*$", re.IGNORECASE)
INLINE_RE = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
LINKED_IMAGE_RE = re.compile(r"\[!\[([^\]]*)\]\(([^)\s]+)\)\]\(([^)\s]+)\)")
TITLE_MARKER_RE = re.compile(r"<!-- NOTE_TITLE_START -->(.*?)<!-- NOTE_TITLE_END -->", re.DOTALL)
BODY_MARKER_RE = re.compile(r"<!-- NOTE_BODY_START -->(.*?)<!-- NOTE_BODY_END -->", re.DOTALL)
IMAGE_SRC_RE = re.compile(r"<img\b[^>]*\bsrc\s*=\s*(['\"])(.*?)\1", re.IGNORECASE | re.DOTALL)


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
        return f'<a href="{html.escape(target, quote=True)}" target="_blank">{label}</a>'

    def replace_linked_image(match: re.Match[str]) -> str:
        label, source, _destination = (html.unescape(value) for value in match.groups())
        return f'<img src="{html.escape(source, quote=True)}" alt="{html.escape(label, quote=True)}">'

    # A linked image is a distinct Markdown construct. Keep its image but not
    # its outer link, and process it before a normal link to avoid broken HTML.
    escaped = LINKED_IMAGE_RE.sub(replace_linked_image, escaped)
    escaped = INLINE_RE.sub(replace_link, escaped)
    # prepare_note_article.py makes Markdown emphasis explicit in article.md.
    # Preserve only that safe, structural markup after escaping the text.
    escaped = (escaped.replace("&lt;strong&gt;", "<strong>")
                      .replace("&lt;/strong&gt;", "</strong>"))
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
            rendered = [inline_html(line, asset_base_url) for line in paragraph]
            output.append("<p>\n" + "\n".join(
                f"    {line}<br>"
                for line in rendered
            ) + "\n</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_kind
        if list_kind:
            output.append(f"</{list_kind}>")
            list_kind = None

    def flush_quote() -> None:
        nonlocal quote_lines
        if quote_lines:
            rendered: list[str] = []
            empty_count = 0
            for quote_line in quote_lines:
                if not quote_line.strip():
                    empty_count += 1
                    continue
                if rendered:
                    # Empty quote lines are intentional visual gaps. Adjacent
                    # non-empty quote lines retain one ordinary line break.
                    rendered.extend(["<br>"] * (empty_count or 1))
                rendered.append(inline_html(quote_line, asset_base_url))
                empty_count = 0
            output.append("<p>\n<blockquote>\n" + "\n".join(rendered) + "\n</blockquote>\n</p>")
            quote_lines = []

    blank_lines = 0
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
            # One blank line in ChatGPT Exporter is a visual line break, not a
            # note paragraph boundary. Use two blanks to begin a new paragraph.
            blank_lines += 1
            if blank_lines >= 2:
                flush_paragraph(); flush_list(); flush_quote()
            continue
        blank_lines = 0
        if line in {"---", "***", "___"}:
            flush_paragraph(); flush_list(); flush_quote(); output.append("<hr>"); continue
        if match := re.match(r"^(#{2,6})\s+(.+)$", line):
            flush_paragraph(); flush_list(); flush_quote()
            level = len(match.group(1))
            output.append(f"<h{level}>{inline_html(match.group(2), asset_base_url)}</h{level}>")
            continue
        if match := re.fullmatch(r"<blockquote>(.*)</blockquote>", line):
            flush_paragraph(); flush_list(); flush_quote()
            output.append("<blockquote>" + inline_html(match.group(1), asset_base_url) + "</blockquote>")
            continue
        if match := re.fullmatch(r">(?: ?)(.*)", line):
            flush_paragraph(); flush_list(); quote_lines.append(match.group(1)); continue
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


def cdata(value: str) -> str:
    return "<![CDATA[" + value.replace("]]>", "]]]]><![CDATA[>") + "]]>"


def wxr_item(article: Path, date: datetime, asset_base_url: str | None) -> str:
    markdown = article.read_text(encoding="utf-8")
    validate_local_assets(article, markdown)
    title, body = markdown_to_html(markdown, asset_base_url)
    return wxr_item_from_html(article.parent.name.split("_", 1)[0], title, body, date)


def wxr_item_from_html(article_number: str, title: str, body: str, date: datetime) -> str:
    timestamp = date.strftime("%Y-%m-%d %H:%M:%S")
    return "\n".join((
        "  <item>",
        f"    <title>{escape(title)}</title>",
        "    <dc:creator><![CDATA[note-article-manager]]></dc:creator>",
        f"    <content:encoded>{cdata(body)}</content:encoded>",
        "    <excerpt:encoded><![CDATA[]]></excerpt:encoded>",
        f"    <wp:post_id>{escape(article_number)}</wp:post_id>",
        f"    <wp:post_date>{timestamp}</wp:post_date>",
        f"    <wp:post_date_gmt>{timestamp}</wp:post_date_gmt>",
        "    <wp:comment_status>closed</wp:comment_status>",
        "    <wp:ping_status>closed</wp:ping_status>",
        f"    <wp:post_name>article-{escape(article_number)}</wp:post_name>",
        "    <wp:status>publish</wp:status>",
        "    <wp:post_parent>0</wp:post_parent>",
        "    <wp:menu_order>0</wp:menu_order>",
        "    <wp:post_type>post</wp:post_type>",
        "    <wp:post_password></wp:post_password>",
        "    <wp:is_sticky>0</wp:is_sticky>",
        "  </item>",
    ))


def wxr_document(entries: list[str]) -> str:
    return "\n".join((
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:wfw="http://wellformedweb.org/CommentAPI/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:wp="http://wordpress.org/export/1.2/">',
        "<channel>",
        "  <title>note-article-manager</title>",
        "  <link>https://note.com/</link>",
        "  <description>note import package</description>",
        "  <language>ja</language>",
        "  <wp:wxr_version>1.2</wp:wxr_version>",
        "  <wp:base_site_url>https://note.com/</wp:base_site_url>",
        "  <wp:base_blog_url>https://note.com/</wp:base_blog_url>",
        *entries,
        "</channel>",
        "</rss>",
        "",
    ))


def html_preview(title: str, body: str) -> str:
    """Create a readable local review artifact; it is never imported directly."""
    return "\n".join((
        "<!DOCTYPE html>",
        '<html lang="ja">',
        "<head>",
        '    <meta charset="utf-8">',
        '    <meta name="viewport" content="width=device-width, initial-scale=1">',
        f"    <title>{html.escape(title)}</title>",
        "",
        "    <style>",
        "        body { background: #f7f7f5; color: #222; font-family: -apple-system, BlinkMacSystemFont, 'Noto Sans JP', sans-serif; line-height: 1.9; margin: 0; }",
        "        article { box-sizing: border-box; max-width: 760px; margin: 0 auto; padding: 48px 28px 96px; background: #fff; min-height: 100vh; }",
        "        h1 { font-size: 2rem; line-height: 1.45; margin: 0 0 2.5rem; }",
        "        h2 { font-size: 1.4rem; line-height: 1.5; margin: 3rem 0 1rem; }",
        "        p { margin: 0 0 1.4rem; }",
        "        blockquote { border-left: 4px solid #ddd; color: #555; margin: 1.6rem 0; padding: .2rem 1.2rem; }",
        "        img { display: block; height: auto; margin: 1.5rem auto; max-width: 100%; }",
        "        pre { background: #f3f4f6; overflow-x: auto; padding: 1rem; }",
        "        code { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }",
        "        hr { border: 0; border-top: 1px solid #ddd; margin: 3rem 0; }",
        "    </style>",
        "</head>",
        "<body>",
        "",
        "    <article>",
        "        <!-- NOTE_TITLE_START -->",
        f"        <h1>{html.escape(title)}</h1>",
        "        <!-- NOTE_TITLE_END -->",
        "",
        "        <!-- NOTE_BODY_START -->",
        "\n".join(f"        {line}" if line else "" for line in body.splitlines()),
        "        <!-- NOTE_BODY_END -->",
        "    </article>",
        "</body>",
        "</html>",
        "",
    ))


class TextOnly(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def plain_text(fragment: str) -> str:
    parser = TextOnly()
    parser.feed(fragment)
    return "".join(parser.parts).strip()


def editable_html_parts(path: Path) -> tuple[str, str]:
    source = path.read_text(encoding="utf-8")
    title_match = TITLE_MARKER_RE.search(source)
    body_match = BODY_MARKER_RE.search(source)
    if not title_match or not body_match:
        raise ValueError("編集HTMLにNOTE_TITLE/NOTE_BODYマーカーがありません。生成済みHTMLを使ってください。")
    title = plain_text(title_match.group(1))
    body = body_match.group(1).strip()
    if not title or not body:
        raise ValueError("編集HTMLのタイトルまたは本文が空です。")
    for _, src in IMAGE_SRC_RE.findall(body):
        if not re.fullmatch(r"https?://[^\s]+", html.unescape(src), re.IGNORECASE):
            raise ValueError(f"本文画像は公開HTTP(S) URLにしてください: {src}")
    return title, body


def main() -> int:
    parser = argparse.ArgumentParser(description="note用HTMLプレビューまたはWXR XMLを生成する")
    parser.add_argument("articles", nargs="+", type=Path, help="記事ディレクトリ、または article.md")
    parser.add_argument("-o", "--output", required=True, type=Path, help="出力する .html または .xml ファイル")
    parser.add_argument("--format", choices=("html", "wxr"), default="wxr", help="html はレビュー用、wxr はnoteインポート用 (既定: wxr)")
    parser.add_argument("--html-source", type=Path, help="WYSIWYG編集後のHTMLをWXR本文として使う")
    parser.add_argument("--asset-base-url", help="table1.png 等を公開している URL のベース")
    parser.add_argument("--date", help="単一記事時の日時上書き (YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--force", action="store_true", help="既存の article.html を上書きして初期HTMLを作り直す")
    args = parser.parse_args()
    expected_suffix = ".html" if args.format == "html" else ".xml"
    if args.output.suffix.lower() != expected_suffix:
        parser.error(f"--format {args.format} の出力ファイルは {expected_suffix} にしてください。")
    if args.format == "html" and len(args.articles) != 1:
        parser.error("HTMLプレビューは単一記事だけ生成できます。")
    if args.html_source and args.format != "wxr":
        parser.error("--html-source は --format wxr と組み合わせてください。")
    if args.html_source and len(args.articles) != 1:
        parser.error("--html-source は単一記事のときだけ指定できます。")
    if args.format == "html" and args.output.exists() and not args.force:
        parser.error("既存の編集HTMLを保護するため上書きしません。作り直す場合だけ --force を指定してください。")
    if args.date and len(args.articles) != 1:
        parser.error("--date は単一記事のときだけ指定できます。")
    try:
        entries = []
        preview: tuple[str, str] | None = None
        for target in args.articles:
            article = target if target.name == "article.md" else target / "article.md"
            if not article.is_file():
                raise ValueError(f"article.md が見つかりません: {article}")
            date = datetime.strptime(args.date, "%Y-%m-%d %H:%M:%S") if args.date else article_date(article)
            if args.html_source:
                if not args.html_source.is_file():
                    raise ValueError(f"編集HTMLが見つかりません: {args.html_source}")
                title, body = editable_html_parts(args.html_source)
                entries.append(wxr_item_from_html(article.parent.name.split("_", 1)[0], title, body, date))
            elif args.format == "html":
                markdown = article.read_text(encoding="utf-8")
                validate_local_assets(article, markdown)
                preview = markdown_to_html(markdown, args.asset_base_url)
            else:
                entries.append(wxr_item(article, date, args.asset_base_url))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rendered = html_preview(*preview) if preview else wxr_document(entries)
    args.output.write_text(rendered, encoding="utf-8", newline="\n")
    suffix = "（HTMLプレビュー）" if args.format == "html" else f"（{len(entries)} 件）"
    print(f"生成しました: {args.output} {suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
