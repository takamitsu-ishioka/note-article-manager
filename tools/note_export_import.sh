#!/bin/bash
# note.com の「エクスポート」で得た zip を展開したディレクトリ(*.xml 1個 + assets/)から、
# 公開済み記事を articles_dir/<3桁番号>_<タイトル>/article.md (frontmatter付き) と画像へ
# 変換し、index_file を再生成する。番号は note の公開日時順。
# articles_dir が既に存在する場合は上書きせず停止する。
# stdout には作成予定(または作成済み)記事の一覧を TSV で出力する。
set -euo pipefail

BASENAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  {
    echo "$BASENAME: $1"
    echo "usage: $BASENAME <export_dir> <articles_dir> <index_file> [--dry-run] [--confirm]"
    echo "example: $BASENAME _export/note_articles articles index.md --dry-run"
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

EXPORT_DIR="${ARGS[0]}"
if [ ! -d "$EXPORT_DIR" ]; then
  echo "$BASENAME: export_dir not found: $EXPORT_DIR" >&2
  echo "$BASENAME: note_articles.zip を unzip したディレクトリを指定してください" >&2
  exit 1
fi

NOTE_EXPORT_IMPORT_BASENAME="$BASENAME" \
  python3 "$SCRIPT_DIR/note_export_import.py" "${ARGS[@]}" "$DRY_RUN" "$CONFIRM"
