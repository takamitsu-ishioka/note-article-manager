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
