#!/bin/bash
# Windows側ブラウザ拡張がエクスポートしたChatGPTセッション(md)を、記事
# ディレクトリのbackup/source.md（元データ）とarticle.md（編集用コピー）へ
# 保存する。記事番号は原稿のtimestamp順でindex.mdに割り当てた番号を渡す。
# 既存の記事ディレクトリへの上書きは行わない。
set -euo pipefail

BASENAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
  {
    echo "$BASENAME: $1"
    echo "usage: $BASENAME <source_file> <article_number> <article_title> [--dry-run] [--confirm]"
    echo "example: $BASENAME /mnt/c/Temp/current_session_with_chatgpt.md 54 '記事タイトル'"
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

if [ "${#ARGS[@]}" -ne 3 ]; then
  usage "Wrong number of arguments"
  exit 1
fi

SOURCE_FILE="${ARGS[0]}"
ARTICLE_NUMBER="${ARGS[1]}"
ARTICLE_TITLE="${ARGS[2]}"
if [[ ! "$ARTICLE_NUMBER" =~ ^[0-9]+$ ]]; then
  usage "article_number must be an integer"
  exit 1
fi
printf -v ARTICLE_NUMBER_PADDED '%03d' "$((10#$ARTICLE_NUMBER))"
DEST_DIR="$REPO_ROOT/articles/${ARTICLE_NUMBER_PADDED}_${ARTICLE_TITLE}"
BACKUP_FILE="$DEST_DIR/backup/source.md"
ARTICLE_FILE="$DEST_DIR/article.md"

if [ ! -f "$SOURCE_FILE" ]; then
  echo "$BASENAME: source file not found: $SOURCE_FILE" >&2
  exit 1
fi

if [ -e "$DEST_DIR" ]; then
  echo "$BASENAME: destination already exists, refusing to overwrite: $DEST_DIR" >&2
  echo "$BASENAME: 別の記事番号を指定するか、既存ファイルを退避してから再実行してください" >&2
  exit 1
fi

echo "$BASENAME: source: $SOURCE_FILE" >&2
echo "$BASENAME: backup: $BACKUP_FILE" >&2
echo "$BASENAME: article: $ARTICLE_FILE" >&2

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

mkdir -p "$DEST_DIR/backup"
cp "$SOURCE_FILE" "$BACKUP_FILE"
cp "$SOURCE_FILE" "$ARTICLE_FILE"
echo "$BASENAME: コピーしました。次は instructions_to_ai_agent.md の" \
     "「ChatGPTセッションをnote投稿可能なmdに変換する最短手順」に従って" \
     "replace.sh / tools/fix_note_quotes.sh をarticle.mdへ実行してください。" >&2
