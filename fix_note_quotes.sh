#!/usr/bin/env bash
# fix_note_quotes.py の薄いラッパー。
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

if [ "$#" -lt 1 ]; then
    cat >&2 <<'EOF'
用途:
  noteに貼り付ける前に、引用(>)ブロック内の「空行」を修正する。
  ">" だけの行に "> " + ゼロ幅スペースを挿入し、noteのパーサーに
  引用ブロックを打ち切らせないようにする（対象ファイルを直接書き換え）。

使い方:
  fix_note_quotes.sh <file.md> [file2.md ...]
EOF
    exit 1
fi

exec python3 "${SCRIPT_DIR}/fix_note_quotes.py" "$@"
