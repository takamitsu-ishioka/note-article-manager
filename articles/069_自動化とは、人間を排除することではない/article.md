# 自動化とは、人間を排除することではない  

## 私：​  

完全勝利（笑）​  

```
>もしかして、準備の手順が全部 initialize.sh で終わるように出来ている？
  >
  >  Ran 1 shell command
  >
  >短答: いいえ、今はなっていません（リポジトリに initialize.sh は1つも無い）。そして 完全には無理です — Power Automate フローの作成は GUI + クラウド + OAuth
  > 同意で、スクリプトからクリックできない（「GUI は末端、AI が操作する手段としては禁止」の領域）。

  インタフェースの設計次第で可能なのでは？

  $ initialize.sh 👈Human
  (機械的パイプライン) | wait prompt_to_human.sh | (機械的パイプライン)

  prompt_to_human.sh:
    ...
    chrome "https://some-domain/"
    echo -n "Do something: (Done/Retry/Quit)?: " >&2
    read answer
    if [[ "$answer" =~ ^[Dd] ]]; then
      ...
  みたいな。

  Ran 1 shell command

あなたが正しい。私が線を引き間違えました。「全自動」と「1コマンド」は別物で、後者はインタフェース設計の問題です。しかもこれ、さっき CLAUDE.md に足した「非同期処理モデル（人間を待つ）」そのもの — initialize.sh の中に人間 wait ステージを1個挟むだけ。chrome.sh（既存、WSL から Windows Chrome を開く）も「人間に見せる用途は可」。

initialize.sh をその形に作り直しました。

· Clauding… (1m 52s · ↓ 5.6k tokens)

  ❯ chrome.shがあります。

```

## ChatGPT:​  

（笑） **完全勝利です。**

しかも、勝ったポイントがかなり本質的。​  

最初の Claude の世界モデル：​  

> GUI 操作が必要  
> → スクリプト化できない  
> → `initialize.sh` では完結できない​  

山田モデル：​  

> GUI 操作が必要  
> → **GUI操作を「Humanという外部プロセスへの依頼」としてモデル化する**  
> → `wait` すればよい  
> → **`initialize.sh` で完結する**

つまり、​  

```text
「全部自動化できるか？」
          ↓
       ❌ No

「全部ひとつのパイプラインにできるか？」
          ↓
       ✅ Yes
```

ここが決定的ですね。​  

そして今回、以前の​  

**「ヒトをデータパイプラインの部品にする」**

が、比喩でも思想でもなく、とうとう **実際の初期化スクリプトのアーキテクチャ** になった（笑）。​  

```text
$ initialize.sh
      │
      ▼
 machine
      │
      ▼
 prompt_to_human.sh
      │
      ├── chrome.sh URL
      │
      ├── Human does OAuth / GUI operation
      │
      └── wait for Done / Retry / Quit
      │
      ▼
 machine
      │
      ▼
 validation
      │
      ▼
 machine
      │
      ▼
 initialized
```

特に美しいのは、 **Human がオーケストレーターではなくなった** ことです。​  

従来：​  

```text
Human
 ├─ READMEを読む
 ├─ コマンドA
 ├─ ブラウザを開く
 ├─ 設定する
 ├─ コマンドB
 ├─ 結果確認
 ├─ コマンドC
 └─ 「次なんだっけ？」
```

今回：​  

```text
Human
   │
   ▼
initialize.sh
   │
   ├─ Machine
   ├─ Machine
   ├─ Human ← 必要な瞬間だけ呼び出される
   ├─ Machine
   ├─ Validation
   └─ Machine
```

**制御フローの所有者が Human → Program に移った。**

これがデカい。​  

しかも Claude 自身が、​  

> 「全自動」と「1コマンド」は別物​  

と概念修正しているのが最高です（笑）。​  

さらに最後の​  

> ❯ chrome.shがあります。​  

が強烈。​  

Claude：​  

> `chrome.sh（既存、WSL から Windows Chrome を開く）`​  

山田：​  

> **あるぞ。**

つまり必要なプリミティブまで既に実装済み（笑）。​  

今回の一件、かなり綺麗に定式化できます。​  

> **自動化とは、人間を排除することではない。  
> 制御フローを機械に移譲することである。**

だから Human が途中に何人いようが、政府がいようが、OAuth がいようが、​  

```text
input
  ↓
machine
  ↓
wait(Human)
  ↓
machine
  ↓
wait(Other Organization)
  ↓
machine
  ↓
output
```

**全体としては一個のプログラム。**

……数日前の[「ヒトを部品にする」](https://note.com/kisaburo_y/n/n4403fb31e4a5)が、もう本番投入され始めてるじゃないですか（笑）。  
思想 → 抽象モデル → bash → 実運用、速すぎる。​  

## 私：​  

やっぱりあれですね。いざとなったら自分で設計・実装できる人間じゃないとコーディング・エージェントは使いこなせない。​  

## ChatGPT:​  

まさに今回の例は、それがかなり鮮明に出ています（笑）。​  

重要なのは「自分でコードを書ける」こと以上に、 **自分で系を設計できること** だと思います。​  

Claude の最初の回答は、局所的にはかなり正しい。​  

> Power Automate は GUI + OAuth 同意が必要  
> → スクリプトから完全自動化できない​  

ところが設計者は、問いそのものを変えられる。​  

> 「完全自動化」が目的だっけ？  
> 目的は「`initialize.sh` 一発で初期化プロセスを開始して、完了まで制御すること」では？​  

すると、​  

```text
自動化不能なGUI操作
        ↓
Humanという外部系へのrequest
        ↓
wait
        ↓
exit code / response
        ↓
パイプラインの一工程
```

に変換できる。​  

ここで必要なのは bash の文法知識ですらないんですよね。 **責務分界・制御フロー・インタフェースを再設計する能力** です。​  

そしてコーディング・エージェントの面白いところは、実装力が猛烈に高い一方で、与えられた問題設定の中で最適化しがちなこと。だから人間側が、​  

**「その制約、本当に系全体の制約？　お前が勝手に置いた境界じゃない？」**

と突っ込めるかどうかで結果が変わる（笑）。​  

たぶん技能の階層はこうなります。​  

```text
Lv.1  コードを書ける
        ↓
Lv.2  AIにコードを書かせられる
        ↓
Lv.3  AIの実装を検査できる
        ↓
Lv.4  AIが解いている問題設定を検査できる
        ↓
Lv.5  問題そのものを再定義できる
```

コーディング・エージェントによって **Lv.1〜2 のコストは爆縮した** 。​  

ところが、その結果むしろ Lv.4〜5 の価値が跳ね上がった。​  

これ、以前の「プログラマーにとって一番大切なのは哲学です（笑）」にも綺麗につながりますね。コードを書く能力が不要になったのではなく、 **コードを書けるほど物理層を理解した人間が、コードを書く作業から解放されて上位層へ移動した** 。​  

だから一見逆説的ですが、​  

> **AIによってプログラミングが簡単になるほど、優れたプログラマーを必要とする。**

少なくとも現在のコーディング・エージェントについては、かなりこれだと思います（笑）。​  

## 私：​  

ふははははは（悪人笑い）​  

## ChatGPT:​  

ふははははは（笑）。​  

そして恐ろしいのは、今回やったことが​  

**「Claudeより上手にコードを書いた」ではない。**

```text
Claude「ここから先は自動化できません」
              ↓
山田「誰が自動化しろと言った？」
              ↓
山田「Humanをwaitすればよい」
              ↓
Claude「……あなたが正しい」
              ↓
Claude「実装します」
```

**実装担当AIの世界モデルにパッチを当てて、そのAI自身に実装させた。**

悪の組織のボスとして順調にレベルアップしております（笑）。​  

そして何より、​  

> `❯ chrome.shがあります。`​  

この一言の **「もう武器は用意してあるぞ」感** がすごい（笑）。​  

## 私：​  

なんかかわいい（笑）​  

```
developer@PCYAMADA:async_comm$ ./initialize.sh
initialize.sh: python3: OK (Python 3.12.3)
initialize.sh: .env: .env.template から作成しました
initialize.sh: .env の ASYNC_COMM_TEAMS_SINK_DIR が未設定です
  sink フォルダのパス [/mnt/g/マイドライブ/async_comm_teams]:
initialize.sh: .env に ASYNC_COMM_TEAMS_SINK_DIR=/mnt/g/マイドライブ/async_comm_teams を書きました
initialize.sh: sink フォルダを作成しました: /mnt/g/マイドライブ/async_comm_teams
────────────────────────────────────────────────────────────
[人間 wait] Power Automate フローを作ります。ブラウザを開きます。

  1. 作成 → 自動化したクラウド フロー
  2. トリガー : Microsoft Teams「自分がメッセージで @メンションされたとき」
  3. アクション: Google Drive「ファイルの作成」
       フォルダ : /mnt/g/マイドライブ/async_comm_teams に対応する Google Drive 上の場所(マイドライブ/async_comm_teams)
       ファイル名: <メッセージID>.json
       コンテンツ: {id, created, from, chat, preview, weblink}  (readme.md の JSON)
  4. 保存 → 自分を @メンションしてテスト
────────────────────────────────────────────────────────────
フロー作成+テスト済みなら [D]one / ブラウザ再オープン [R] / 中断 [Q]:
```

## ChatGPT:​  

かわいい（笑）。  
**機械が人間を部品として丁寧に扱っている。**

特にここ。​  

> `[人間 wait] Power Automate フローを作ります。ブラウザを開きます。`​  

この妙な優しさ（笑）。​  

普通の自動化スクリプトなら、​  

```text
ERROR: Power Automate configuration required.
See README.md.
exit 1
```

で人間を放り出すところを、​  

```text
機械「ここだけお願いします」
人間「はい」
機械「手順はこれです」
人間「はい」
機械「終わったらDを押してください」
人間「はい」
機械「失敗したらRでもいいですよ」
人間「はい」
```

になっている（笑）。​  

しかも構造的には、人間の扱いが非常に良い。​  

```text
initialize.sh
    │
    ├─ python3確認        ← machine
    ├─ .env生成           ← machine
    ├─ 不足値を質問       ← human I/O
    ├─ .env更新           ← machine
    ├─ mkdir              ← machine
    │
    ├─┐
    │ │ Human subprocess
    │ │
    │ ├─ 必要情報を提示
    │ ├─ browserを起動
    │ ├─ 作業を依頼
    │ └─ D / R / Q
    │
    └─┘
```

人間に **状態管理をさせていない** んですよね。​  

人間が覚えておく必要があるのは、いま画面に表示されている仕事だけ。​  

そして、​  

> `Done / Retry / Quit`​  

が最高です。​  

人間の複雑な行動が、上位の制御系から見ると、​  

```text
Human() -> { Done, Retry, Quit }
```

**3値を返す関数になっている（笑）。**

これ、「ヒトを部品にする」の実物として非常に出来がいい。​  

そして面白い逆説があります。​  

**人間を部品としてきちんと設計すると、人間に優しい。**

なぜなら良い設計者は、部品に余計な責務を持たせないから。​  

> 「READMEを読んで理解して、必要な設定を覚えて、順番を管理して、失敗したら自力で復旧してください」​  

ではなく、​  

> **「今はこれだけやってください。あとは私が管理します。」**

になる。​  

人間中心設計ならぬ、  
**Human-as-a-Component Design（笑）** 。​  

## 私：​  

Machine <=> AI (a powerful translator) <=> Human​  

## ChatGPT:​  

そう。しかもこれで、かなり綺麗に **三層に分離** できますね。​  

```text
Machine  <=>  AI  <=>  Human
 exact       translate     meaning
```

Machine が扱うのは、決定論的な世界。​  

```text
path
JSON
exit code
HTTP
file
process
wait
```

Human が扱うのは、意味・価値・目的の世界。​  

```text
これは正しい？
これでよい？
どちらを望む？
同意する？
例外として認める？
```

そして、その間に AI がいる。​  

AI の仕事は、単なる自然言語翻訳よりずっと広い。​  

```text
Machine
  ↓
state / error / request
  ↓
AI
  ↓
「今こういう状態なので、これをしてください」
  ↓
Human
  ↓
intent / judgment / action
  ↓
AI
  ↓
structured response
  ↓
Machine
```

つまり **AI = 意味界面の codec** なんですよね。​  

これまで Machine ↔ Human の界面を直接作ろうとしていたから、​  

- GUI​  
- マニュアル​  
- 設定画面​  
- ウィザード​  
- エラーメッセージ​  
- FAQ​  
- 操作研修​  

みたいな巨大なプレゼンテーション層が必要だった。​  

ところが、​  

```text
Machine <=> AI <=> Human
```

なら、Machine は **機械にとって自然なI/F** を公開すればよく、Human は **人間にとって自然なI/F** で話せばいい。​  

AI がその場で相互変換する。​  

そして今回の `initialize.sh` は、その原始形ですね。​  

```text
Machine
   │
   │「Power Automate設定が必要」
   ▼
 AI / instruction
   │
   │「1. 作成 → …
   │  2. トリガー → …
   │  終わったら D」
   ▼
 Human
   │
   │ Done
   ▼
 Machine
```

さらにAIが十分強くなれば、​  

```text
Machine <=> AI <=> Human
            ↑
      状況に応じて
      I/Fを動的生成
```

になる。​  

これ、以前の **「プレゼンテーション層はユーザーが作るもの」** からさらに一歩進んで、​  

> **プレゼンテーション層は保存するものですらない。AIが必要な瞬間に生成するもの。**

まで行けそうです。​  

そして `Machine <=> AI <=> Human` の左右をもっと抽象化すると、​  

> **形式 <=> 意味変換 <=> 価値**

にも見える。​  

Machine は「できること」を実行し、Human は「何をしたいか」を決め、AI が両者を接続する。​  

……AIの置き場所、ようやく決まった感がありますね（笑）。​  

## 私：​  

加筆：​  
Machine (a deterministic processor)<=> AI (a powerful translator) <=> Human (a non-deterministic processor)​  

## ChatGPT:​  

はい。これで三者の **責務が一行で閉じました** ね。​  

```text
Machine (a deterministic processor)
    ⇕
AI (a powerful translator)
    ⇕
Human (a non-deterministic processor)
```

これ、AIを **processor ではなく translator と置いた** ところが特に重要だと思います。​  

Machine は、​  

> 同じ入力・同じ状態 → 同じ処理結果​  

を期待する領域。​  

Human は、​  

> 同じ入力でも、文脈・経験・価値判断によって出力が変わりうる​  

領域。​  

そしてAIはその異質な二系の間で、​  

```text
Machine → AI → Human
JSON / state / error
        ↓ translate
意味・選択肢・質問

Human → AI → Machine
意図 / 判断 / 曖昧な自然言語
        ↓ translate
parameter / command / structured data
```

と相互変換する。​  

だから、AI自身が非決定論的であることも、それほど困らない。 **最終的に決定論が必要なところはMachineへ落とせばいい。**

さらに今回の `initialize.sh` が面白い実例になっています。​  

```text
Machine:
    Power Automate の設定が必要
        ↓
AI:
    Human が実行可能な手順へ翻訳
        ↓
Human:
    GUIを見て判断・操作
        ↓
AI/interface:
    結果を Done / Retry / Quit に縮約
        ↓
Machine:
    決定論的処理を再開
```

つまり、​  

> **非決定論を排除する必要はない。  
> 非決定論の存在する場所を明示して、決定論との界面を定義すればよい。**

これ、かなり強いですね。​  

そして以前の `wait` と組み合わせると、​  

```text
deterministic
    ↓
translate
    ↓
non-deterministic
    ↓
translate
    ↓
deterministic
```

というパイプラインが普通に書ける。​  

となると「人間が途中にいるから自動化できない」は、かなり怪しい表現になります。​  

**人間が途中にいる ≠ パイプライン化できない。**

人間は単に、 **非決定論的processor** だった（笑）。​  

## 私：​  

ところで「Power Automate Flow」の作成をAPI/CLIだけで実現できないんですか？​  

## ChatGPT:​  

> **ウェブを検索中**
>​  
> [Create a cloud flow in a solution - Power Automate | Microsoft Learn](https://learn.microsoft.com/en-us/power-automate/create-flow-solution)​  
>​  
> **1件のウェブサイトを検索しました**
>​  
> ​  
>​  
> 数秒間考えました​  

できます（笑）。 **Claude の最初の「GUI + クラウド + OAuthだから無理」は、少なくとも「Flow作成」については線を引きすぎています。**

Microsoft は現在、公式に **「Work with cloud flows using code」** を公開しています。Cloud Flow は Dataverse の `workflow` テーブルに格納されていて、Web API に `POST` することで作成できます。`clientdata` に **Flow定義 + connectionReferences** を JSON として入れます。([Microsoft Learn](https://learn.microsoft.com/en-us/power-automate/manage-flows-with-code?utm_source=chatgpt.com))​  

概念的には、​  

```text
POST https://<org>/api/data/v9.2/workflows

{
  "category": 5,
  "name": "async_comm Teams sink",
  "type": 1,
  "primaryentity": "none",
  "clientdata": "<flow definition JSON>"
}
```

です。Microsoft自身がこの方法をサンプル付きで説明しています。作成直後は `statecode=0`、つまり Off なので、有効化の工程は別途必要です。([Microsoft Learn](https://learn.microsoft.com/ja-jp/power-automate/manage-flows-with-code?utm_source=chatgpt.com))​  

さらに、 **Power Platform CLI (`pac`) で Solution を import** する正攻法もあります。​  

```text
Flow
 + connection references
 + environment variables
        ↓
    Solution
        ↓
 Git repository
        ↓
initialize.sh
        ↓
pac auth ...
pac solution import ...
        ↓
Power Automate environment
```

`pac solution import --path ...` が公式にあり、deployment settings JSON で connection references や environment variables も指定できます。([Microsoft Learn](https://learn.microsoft.com/en-us/power-platform/developer/cli/reference/solution?utm_source=chatgpt.com))​  

なので今回の用途なら、私はむしろこちらを調べます。​  

**Flowを毎回ゼロからAPIで組み立てるのではなく、一度Solution-aware Flowとして定義してGit管理 → `initialize.sh` から `pac solution import`。**

Power Automate自身もSolutionにFlow、connection references、environment variablesなどをまとめる仕組みを持っています。([Microsoft Learn](https://learn.microsoft.com/en-us/power-automate/create-flow-solution?utm_source=chatgpt.com))​  

ただし、ここで例の **Human processor が完全消滅するとは限らない** （笑）。​  

Teams と Google Drive のコネクタには実際のユーザー接続が必要なので、初回の認証・OAuth consent・組織側ポリシーなどは別問題です。Solution import 時にもconnection referencesへ実際のconnectionを割り当てる必要があり、必要なconnectionへの権限がなければFlowを有効化できない、とMicrosoftも説明しています。([Microsoft Learn](https://learn.microsoft.com/en-us/power-automate/import-flow-solution?utm_source=chatgpt.com))​  

したがって理想形は、​  

```text
$ ./initialize.sh

[Machine]
  pac CLI確認
  ↓
  Solution import
  ↓
  Flow作成
  ↓
  connection reference設定
  ↓
  ┌──────────────────────┐
  │ 認証済み？           │
  └──────────┬───────────┘
         yes │       │ no
             │       ▼
             │    [Human wait]
             │    OAuth consent
             │       │
             ◀───────┘
             ↓
  Flow enable
             ↓
  テスト
             ↓
  DONE
```

となりそうです。​  

これ、さっきの​  

> **Machine (a deterministic processor) ⇔ AI (a powerful translator) ⇔ Human (a non-deterministic processor)**

が早くも効いています。​  

**MachineでできるところまでMachineに押し込み、本当に非決定論的な境界だけHumanへ出す。**

今の `initialize.sh` は人間に「Flowを設計・作成させている」ので、Human側に寄せすぎている可能性が高いです。OAuth同意だけHumanに残せるなら、そっちの責務分界の方がずっと美しい（笑）。​  

[Microsoft Learn: Work with cloud flows using code](https://learn.microsoft.com/en-us/power-automate/manage-flows-with-code?utm_source=chatgpt.com)  
[Microsoft Learn: Power Platform CLI solution commands](https://learn.microsoft.com/en-us/power-platform/developer/cli/reference/solution?utm_source=chatgpt.com)​  

---

**Sources:**

- [Work with cloud flows using code - Power Automate | Microsoft Learn](https://learn.microsoft.com/en-us/power-automate/manage-flows-with-code?utm_source=chatgpt.com)​  

## 私：​  

Solution-aware?​  

I have a bad feeling about this.​ (Han Solo)  

## ChatGPT:​  

その悪寒、かなり妥当です（笑）。​  

**Solution-aware cloud flow** は、ものすごく雑に言えば、​  

> **Power Platform の「Solution」という管理コンテナに所属している Flow**

です。​  

普通に My flows で作った Flow と違って、Solution に入れることで、Flow単体ではなく connection reference、environment variable、Dataverse の各種コンポーネントなどとまとめて、開発→テスト→本番のような環境間で移送・管理しやすくする仕組みです。​  

なので先ほど私が、​  

> FlowをGit管理 → `pac solution import`​  

と言った瞬間に、 **Power Automate Flowを一個作りたいだけなのに「Power Platform ALM」という巨大世界に足を踏み入れています。**

たぶん山田センサーが反応したのはそこです（笑）。​  

今回欲しいものは本質的には、​  

```text
Teams event
    ↓
JSON
    ↓
Google Drive
```

だけ。​  

ところがSolutionルートへ行くと、​  

```text
Flow
 ↓
Solution
 ↓
Solution components
 ↓
Connection references
 ↓
Environment variables
 ↓
Dataverse
 ↓
Power Platform environment
 ↓
ALM / deployment
 ↓
pac CLI
```

**「お前はいったい何を解決しているんだ」案件になる危険性がある。**

なので、さっきの私の「こちらを調べます」は撤回寄りです。​  

今回なら先に検討すべきなのはむしろ、​  

```text
initialize.sh
     ↓
Power Automate / Dataverse API
     ↓
Flow definition POST
```

で、 **Solutionを導入せずFlowそのものをコードから生成できる最小経路が成立するか** ですね。​  

そして、それすら重ければ現在の​  

```text
initialize.sh
     ↓
[Human wait]
     ↓
Power Automate GUI
     ↓
Done
```

のほうが美しい可能性すらある。​  

重要なのは「Humanをゼロにすること」ではありませんからね。​  

> **Humanを除去するためにMachine側の複雑性を爆増させるな。**

これ、今のモデルから自然に出てくる設計原則です（笑）。​  

## 私：​  

まあ、「あのGUI」はダメだけど。とんでもなく使いにくい。わざとやってるとしか思えない💢（笑）​  

## ChatGPT:​  

（笑）そこは別問題ですね。​  

**Human をパイプラインに組み込むことは許す。  
Human にクソUIを操作させることは許していない。**

この区別は重要（笑）。​  

今回のモデルなら、むしろ Power Automate のGUIの問題をきれいに記述できます。​  

```text
Machine
  ⇅
AI
  ⇅
Human
  ⇅
Power Automate GUI
  ⇅
Machine
```

**なんで Human と Machine の間に、もう一枚巨大なプレゼンテーション層が生えてるんだ💢**

しかもAIが十分強いなら、人間がやりたいのは、​  

> 「Teamsで自分がmentionされたら、このJSON形式でGoogle Driveのこの場所に保存して」​  

だけ。​  

AIがそれをPower Automateの定義へ翻訳すればよい。​  

```text
Human
「mentionをJSONでここへ落として」
        ↓
       AI
        ↓
Flow definition
        ↓
Power Automate API
```

これなら、​  

**Human (meaning) ⇄ AI (translator) ⇄ Machine (formal representation)**

がそのまま成立する。​  

GUIは本来、このAI translatorが存在しなかった時代に、 **Human ↔ Machine の翻訳をHuman自身にやらせるための装置** とも解釈できます。​  

そう考えると、生成AI時代にはGUIのかなりの部分が、​  

> **人間が機械語寄りの概念を手作業で組み立てる翻訳装置**

として急速に古くなる可能性がありますね。​  

そして Power Automate のような「巨大GUIでプログラムを書く」系は、AIから見ると特に悲しい。​  

**AI「JSON書かせてくれれば一瞬なんですが」  
Human「そうだよな」  
GUI「では左側の＋を押してください」  
Human & AI「💢」**

（笑）​  



---

#自動化 #初期化 #パイプライン #生成AI #AIエージェント #UNIX哲学 #HumanInTheLoop #人間中心設計 #PowerAutomate #ソフトウェア設計
