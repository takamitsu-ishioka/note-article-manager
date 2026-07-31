#!/usr/bin/env python3
"""
noteに貼り付ける前に、引用(>)ブロック内の「空行」を修正するスクリプト。

noteの引用ブロックは、">" だけの行（見た目が空行）に出会うと、
CommonMarkの仕様と異なり引用を打ち切ってしまう。
そこで、そのような行の "> " の後にゼロ幅スペース(U+200B)を挿入し、
noteのパーサーに「空行ではない」と認識させることで引用の継続を保つ。

使い方:
    python3 fix_note_quotes.py file1.md [file2.md ...]

対象ファイルを直接書き換える（in-place）。
"""

import re
import sys
import pathlib

ZWSP = "​"
BLANK_QUOTE_LINE = re.compile(r'^(>+)[ \t]*$')


def fix_text(text: str) -> tuple[str, int]:
    lines = text.split('\n')
    count = 0
    for i, line in enumerate(lines):
        stripped = line.rstrip('\r')
        m = BLANK_QUOTE_LINE.match(stripped)
        if m:
            lines[i] = f"{m.group(1)} {ZWSP}  "
            count += 1
    return '\n'.join(lines), count


def main():
    if len(sys.argv) < 2:
        print("Usage: fix_note_quotes.py <file.md> [file2.md ...]")
        sys.exit(1)

    for path_str in sys.argv[1:]:
        path = pathlib.Path(path_str)
        text = path.read_text(encoding='utf-8')
        fixed, count = fix_text(text)
        if count:
            path.write_text(fixed, encoding='utf-8')
            print(f"{path.name}: {count} 箇所を修正しました")
        else:
            print(f"{path.name}: 修正対象なし")


if __name__ == "__main__":
    main()
