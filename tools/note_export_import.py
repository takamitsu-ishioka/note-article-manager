"""Rebuild article directories and index.md from a note.com export (WXR XML + assets/).

Called only from note_export_import.sh.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

NS = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}
BASENAME = os.environ.get("NOTE_EXPORT_IMPORT_BASENAME", "note_export_import.sh")
MAX_DIR_NAME_BYTES = 200


def log(message: str) -> None:
    print(message, file=sys.stderr)


def progress(index: int, total: int, message: str) -> None:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log(f"{now} {index}/{total} {message}")


# ---------------------------------------------------------------- HTML -> tree

class Node:
    def __init__(self, tag: str, attrs: dict[str, str] | None = None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children: list[Node | str] = []


VOID_TAGS = {"br", "img", "hr"}


class TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("root")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: v or "" for k, v in attrs})
        self.stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, {k: v or "" for k, v in attrs}))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


# ---------------------------------------------------------------- tree -> markdown

BLOCK_TAGS = {"p", "h2", "h3", "ul", "ol", "li", "blockquote", "figure", "pre", "hr"}
KNOWN_TAGS = BLOCK_TAGS | {"root", "br", "strong", "s", "a", "img", "figcaption", "code"}


class Converter:
    def __init__(self) -> None:
        self.images: list[str] = []
        self.unknown_tags: set[str] = set()

    def inline(self, node: Node) -> str:
        out = []
        for child in node.children:
            if isinstance(child, str):
                out.append(child.replace("\n", " "))
                continue
            tag = child.tag
            if tag not in KNOWN_TAGS:
                self.unknown_tags.add(tag)
            if tag == "br":
                out.append("  \n")
            elif tag == "strong":
                out.append(f"**{self.inline(child)}**")
            elif tag == "s":
                out.append(f"~~{self.inline(child)}~~")
            elif tag == "code":
                out.append(f"`{self.inline(child)}`")
            elif tag == "a":
                out.append(f"[{self.inline(child)}]({child.attrs.get('href', '')})")
            elif tag == "img":
                out.append(self.image(child, ""))
            else:
                out.append(self.inline(child))
        return "".join(out)

    def image(self, node: Node, caption: str) -> str:
        name = Path(node.attrs.get("src", "")).name
        self.images.append(name)
        return f"![{caption}]({name})"

    def blocks(self, node: Node) -> list[str]:
        """Render block-level children; each element is one markdown block."""
        out: list[str] = []
        pending_inline: list[Node | str] = []

        def flush() -> None:
            if pending_inline:
                text = self.inline(_wrap(pending_inline)).strip()
                if text:
                    out.append(text)
                pending_inline.clear()

        for child in node.children:
            if isinstance(child, str) or child.tag not in BLOCK_TAGS:
                pending_inline.append(child)
                continue
            flush()
            out.extend(self.block(child))
        flush()
        return out

    def block(self, node: Node) -> list[str]:
        tag = node.tag
        if tag == "p":
            text = self.inline(node).strip()
            return [text] if text else []
        if tag in ("h2", "h3"):
            return [f"{'#' * int(tag[1])} {self.inline(node).strip()}"]
        if tag == "hr":
            return ["---"]
        if tag == "pre":
            code = "".join(_text(node)).rstrip("\n")
            fence = "~~~~" if "```" in code else "```"
            return [f"{fence}\n{code}\n{fence}"]
        if tag in ("ul", "ol"):
            return ["\n".join(self.list_lines(node, 0))]
        if tag == "blockquote":
            inner = "\n\n".join(self.blocks(node))
            return ["\n".join(f"> {line}" if line else ">" for line in inner.split("\n"))]
        if tag == "figure":
            caption_nodes = [c for c in node.children if isinstance(c, Node) and c.tag == "figcaption"]
            caption = self.inline(caption_nodes[0]).strip() if caption_nodes else ""
            out: list[str] = []
            for child in node.children:
                if isinstance(child, Node) and child.tag == "img":
                    out.append(self.image(child, caption))
                elif isinstance(child, Node) and child.tag != "figcaption":
                    out.extend(self.block(child) if child.tag in BLOCK_TAGS else [self.inline(child)])
                    if caption:
                        out.append(f"*{caption}*")
            return out
        if tag == "li":
            return self.blocks(node)
        self.unknown_tags.add(tag)
        return self.blocks(node)

    def list_lines(self, node: Node, depth: int) -> list[str]:
        lines: list[str] = []
        number = 0
        for li in node.children:
            if not isinstance(li, Node) or li.tag != "li":
                continue
            number += 1
            marker = f"{number}." if node.tag == "ol" else "-"
            indent = "  " * depth
            text_parts: list[Node | str] = []
            nested: list[Node] = []
            for c in li.children:
                if isinstance(c, Node) and c.tag in ("ul", "ol"):
                    nested.append(c)
                else:
                    text_parts.append(c)
            text = "\n\n".join(self.blocks(_wrap(text_parts)))
            cont = indent + " " * (len(marker) + 1)
            text_lines = text.split("\n") or [""]
            lines.append(f"{indent}{marker} {text_lines[0]}")
            lines.extend(f"{cont}{line}" if line else "" for line in text_lines[1:])
            for sub in nested:
                lines.extend(self.list_lines(sub, depth + 1))
        return lines


def _wrap(children: list[Node | str]) -> Node:
    node = Node("span")
    node.children = list(children)
    return node


def _text(node: Node) -> list[str]:
    out = []
    for c in node.children:
        if isinstance(c, str):
            out.append(c)
        elif c.tag == "br":
            out.append("\n")
        else:
            out.extend(_text(c))
    return out


TITLE_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


def html_to_markdown(html: str) -> tuple[str, str, list[str], set[str]]:
    """Return (body, title_image, body_images, unknown_tags).

    note のエクスポートには見出し画像の専用欄が無く、本文先頭の画像として入っている。
    本文の最初のブロックが画像だけなら、それを見出し画像として本文から外す。
    """
    builder = TreeBuilder()
    builder.feed(html)
    builder.close()
    conv = Converter()
    blocks = conv.blocks(builder.root)
    title_image = ""
    if blocks and (m := TITLE_IMAGE_RE.fullmatch(blocks[0])):
        title_image = m.group(1)
        blocks.pop(0)
        conv.images.remove(title_image)
    return "\n\n".join(blocks) + "\n", title_image, conv.images, conv.unknown_tags


# ---------------------------------------------------------------- plan / write

def safe_dir_name(number: int, title: str) -> str:
    name = re.sub(r"[\x00-\x1f​﻿]", "", title).replace("/", "／").strip() or "untitled"
    name = f"{number:03d}_{name}"
    while len(name.encode("utf-8")) > MAX_DIR_NAME_BYTES:
        name = name[:-1]
    return name.rstrip(". ")


def load_items(xml_file: Path) -> list[dict[str, str]]:
    root = ET.parse(xml_file).getroot()
    items = []
    for it in root.findall("./channel/item"):
        if it.findtext("wp:status", namespaces=NS) != "publish":
            continue
        items.append({
            "title": (it.findtext("title") or "").strip(),
            "guid": (it.findtext("guid") or "").strip(),
            "url": (it.findtext("link") or "").strip(),
            "published": it.findtext("wp:post_date", namespaces=NS) or "",
            "modified": it.findtext("wp:post_modified", namespaces=NS) or "",
            "post_id": it.findtext("wp:post_id", namespaces=NS) or "0",
            "html": it.findtext("content:encoded", namespaces=NS) or "",
        })
    items.sort(key=lambda x: (x["published"], int(x["post_id"])))
    return items


def frontmatter(item: dict[str, str]) -> str:
    keys = ("title", "guid", "url", "published", "modified")
    return "---\n" + "".join(f"{k}: {json.dumps(item[k], ensure_ascii=False)}\n" for k in keys) + "---\n"


def main() -> int:
    if len(sys.argv) != 6:
        log(f"{BASENAME}: internal error: bad arguments to python")
        return 2
    export_dir, articles_dir, index_file = map(Path, sys.argv[1:4])
    dry_run = sys.argv[4] == "true"
    confirm = sys.argv[5] == "true"

    xml_files = sorted(export_dir.glob("*.xml"))
    assets_dir = export_dir / "assets"
    if len(xml_files) != 1:
        log(f"{BASENAME}: expected exactly one *.xml in {export_dir}, found {len(xml_files)}")
        log(f"{BASENAME}: note のエクスポート zip を展開したディレクトリを指定してください")
        return 1
    if articles_dir.exists():
        log(f"{BASENAME}: articles_dir already exists, refusing to overwrite: {articles_dir}")
        log(f"{BASENAME}: 退避(mv)してから再実行してください")
        return 1

    items = load_items(xml_files[0])
    plans = []
    missing_images: list[str] = []
    unknown_tags: set[str] = set()
    for n, item in enumerate(items, start=1):
        body, title_image, images, unknown = html_to_markdown(item["html"])
        unknown_tags |= unknown
        missing_images += [f"{item['guid']}/{name}" for name in [title_image, *images]
                           if name and not (assets_dir / name).is_file()]
        plans.append((n, item, safe_dir_name(n, item["title"]), body, title_image, images))

    log(f"{BASENAME}: ---- 入出力諸元 ----")
    log(f"{BASENAME}: input  xml     : {xml_files[0]}")
    log(f"{BASENAME}: input  assets  : {assets_dir}")
    log(f"{BASENAME}: output articles: {articles_dir} (新規作成, {len(plans)} 記事)")
    log(f"{BASENAME}: output index   : {index_file} ({'上書き' if index_file.exists() else '新規作成'})")
    log(f"{BASENAME}: title images   : {sum(1 for p in plans if p[4])} (title.png)")
    log(f"{BASENAME}: body images    : {sum(len(p[5]) for p in plans)}")
    log(f"{BASENAME}: missing images : {len(missing_images)}")
    log(f"{BASENAME}: unknown tags   : {sorted(unknown_tags) or 'none'}")
    for m in missing_images:
        log(f"{BASENAME}: missing image: {m}")

    print("number\tpublished\tguid\ttitle_image\tbody_images\tdir")
    for n, item, dir_name, _, title_image, images in plans:
        print(f"{n}\t{item['published']}\t{item['guid']}\t{'yes' if title_image else 'no'}\t{len(images)}\t{dir_name}")

    if dry_run:
        log(f"{BASENAME}: (dry-run: 何も書き込んでいません)")
        log(f"{BASENAME}: 次: 一覧を確認し、--dry-run を外して再実行してください")
        return 0
    if confirm:
        with open("/dev/tty") as tty:
            sys.stderr.write("上記のとおり作成しますか？ [y/N] ")
            sys.stderr.flush()
            if tty.readline().strip() not in ("y", "Y"):
                log(f"{BASENAME}: Aborted.")
                return 1

    articles_dir.mkdir(parents=True)
    index_lines = [
        "# 記事索引",
        "",
        "note のエクスポートから tools/note_export_import.sh で生成。手で編集しないこと。"
        "番号は note の公開日時順。",
        "",
    ]
    for n, item, dir_name, body, title_image, images in plans:
        progress(n, len(plans), dir_name)
        dest = articles_dir / dir_name
        dest.mkdir()
        (dest / "article.md").write_text(
            frontmatter(item) + "\n# " + item["title"] + "\n\n" + body, encoding="utf-8")
        if title_image and (assets_dir / title_image).is_file():
            shutil.copy2(assets_dir / title_image, dest / "title.png")
        for name in dict.fromkeys(images):
            if (assets_dir / name).is_file():
                shutil.copy2(assets_dir / name, dest / name)
        link = os.path.relpath(dest / "article.md", index_file.parent)
        index_lines.append(f"{n}. {item['published']} — [{item['title']}](<{link}>)")
    index_file.write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    log(f"{BASENAME}: 完了: {len(plans)} 記事を {articles_dir} に作成し、{index_file} を書き出しました")
    log(f"{BASENAME}: 次: git status / git diff で確認し、問題なければ commit してください")
    return 0


if __name__ == "__main__":
    sys.exit(main())
