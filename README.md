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

## noteへの投稿

投稿はコピー＆ペーストではなく、note公式の「インポート」を使う。`article.md`から
Movable Type (MT) 形式の `.txt` を生成し、noteへアップロードすると、記事は**下書き**として
追加される。公開ボタンを押すことだけは、必ずnote上で人が判断する。

```bash
python3 tools/export_note_import.py \
  'articles/139_認証なんか要らない。商売をしろ！（笑）' \
  --output exports/note-139.txt
```

このリポジトリにしかない表・図などの `TODO: table1.png` は、noteが取得できる公開 HTTPS URL が必要である。
アセットを公開済みの場合は、その記事用のURLを明示する。

```bash
python3 tools/export_note_import.py \
  'articles/143_①神を僭称するな💢②束ねるな💢' \
  --asset-base-url 'https://assets.example.com/note/143' \
  --output exports/note-143.txt
```

`exports/` は生成物としてGit管理しない。noteの「自分の記事」→「インポート」で **MT形式** を選び、
生成した `.txt` をアップロードする。結果メールを待ち、下書きで本文・画像・日時を確認してから公開する。
インポートファイルの上限は20MB・1000記事で、同時実行はできない。タイトル画像は本文画像とは別物で、
このリポジトリから作る新規記事ではインポート後にnoteの編集画面で設定する。

既存のnote記事を移す場合は別経路である。note公式エクスポートが作るZIPを展開し、中のWXR `.xml` を
**WXR形式** としてインポートする。ZIPや`assets/`フォルダ自体はアップロードしない。画像を含むWXRの
再取り込み可否はXML中の`img src`がHTTP(S)のJPEG/PNG/GIF URLであることに依存するため、移行前に
1記事で確認する。なおnote公式エクスポートには見出し画像・ハッシュタグなどのnote固有設定は含まれない。

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
