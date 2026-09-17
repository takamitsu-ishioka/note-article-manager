# note-article-manager

note投稿原稿と関連アーティファクトを、記事単位で管理するリポジトリです。

## 構造

```text
note-article-manager/
├── README.md
├── index.md
├── instructions_to_ai_agent.md
├── templates/
├── tools/
├── articles/
│   └── <timestamp順の3桁番号>_<記事タイトル>/
│       ├── article.md
│       ├── backup/
│       ├── title.png
│       ├── table*.png
│       └── その他の関連アーティファクト
└── trash/
```

記事の入口は[index.md](index.md)です。番号は原稿のtimestamp順であり、旧シリーズ番号とは無関係です。

原稿の編集・取り込み・画像生成については[instructions_to_ai_agent.md](instructions_to_ai_agent.md)を参照してください。対応記事を特定できない旧ファイルは、誤って関連付けず`trash/`へ退避します。

## 用語集候補の抽出

想定読者を「専門知識を前提としない高校生以上」とし、記事から説明候補を抽出できます。
SudachiPyで語を分割し、一般文書を基にしたwordfreqの日本語頻度辞書を直接参照して、
頻度が低い語を優先します。日本語の再分割は行わないため、MeCabは不要です。

```bash
sudo python3 -m pip install --break-system-packages -r requirements-glossary.txt
python3 tools/extract_glossary_candidates.py articles/<記事ディレクトリ>/article.md
```

結果は記事と同じディレクトリの`glossary.json`へ出力されます。これは登録候補であり、
採否と記事内に表示する説明文はレビューで確定します。候補数と最低スコアは
`--limit`と`--threshold`で変更できます。
