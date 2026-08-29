#!/bin/bash
# ブラウザ拡張がエクスポートしたChatGPTセッション
# (/mnt/c/Temp/current_session_with_chatgpt.md) を、タイトルと現在時刻から
# 生成したファイル名で drafts/ へコピーする。記事番号を確定する前の、下書き
# 置き場への最短ショートカット。既存ファイルへの上書きは行わない。
set -euo pipefail

BASENAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_FILE="/mnt/c/Temp/current_session_with_chatgpt.md"

usage() {
  {
    echo "$BASENAME: $1"
    echo "usage: $BASENAME <title> [--dry-run] [--confirm]"
    echo "example: $BASENAME '「正規化」で通じるのが恐い'"
    echo
    awk 'NR>1 && /^#/{sub(/^# ?/,""); print; next} NR>1{exit}' "$0"
  } >&2
}

DRY_RUN=false
CONFIRM=false
ARGS=()
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --confirm) CONFIRM=true ;;
    --*)
      usage "Unknown option: $arg"
      exit 1
      ;;
    *) ARGS+=("$arg") ;;
  esac
done

if [ "${#ARGS[@]}" -ne 1 ]; then
  usage "Wrong number of arguments"
  exit 1
fi

TITLE="${ARGS[0]}"
if [ -z "$TITLE" ] || [[ "$TITLE" == */* ]]; then
  usage "title must be non-empty and must not contain '/'"
  exit 1
fi

TIMESTAMP="$(date +%Y-%m-%dT%H:%M:%S)"
DEST_FILE="$REPO_ROOT/drafts/${TITLE}-${TIMESTAMP}.md"

if [ ! -f "$SOURCE_FILE" ]; then
  echo "$BASENAME: source file not found: $SOURCE_FILE" >&2
  exit 1
fi

if [ -e "$DEST_FILE" ]; then
  echo "$BASENAME: destination already exists, refusing to overwrite: $DEST_FILE" >&2
  exit 1
fi

echo "$BASENAME: source: $SOURCE_FILE" >&2
echo "$BASENAME: dest:   $DEST_FILE" >&2

if "$DRY_RUN"; then
  echo "$BASENAME: (dry-run: コピーは行いません)" >&2
  exit 0
fi

if "$CONFIRM"; then
  read -r -p "上記のとおりコピーしますか？ [y/N] " answer
  if [[ "$answer" != "y" && "$answer" != "Y" ]]; then
    echo "$BASENAME: Aborted." >&2
    exit 1
  fi
fi

cp "$SOURCE_FILE" "$DEST_FILE"
echo "$BASENAME: コピーしました: $DEST_FILE" >&2
echo "$BASENAME: 次は instructions_to_ai_agent.md の「ChatGPTセッションをnote投稿可能な" \
     "mdに変換する最短手順」に従って replace.sh / tools/fix_note_quotes.sh を実行してください。" >&2
