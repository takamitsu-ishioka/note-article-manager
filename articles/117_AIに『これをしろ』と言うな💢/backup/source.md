# AIに『これをしろ』と言うな💢
## 「こんなことで困っている」と言え。AI使いこなしの極意。

**User:** y.kisaburo@gmail.com  
**Created:** 10/9/2026 4:10:35  
**Updated:** 10/9/2026 5:24:42  
**Exported:** 10/9/2026 5:27:21  

## Prompt:
2026/10/9 4:12:44

AI使いこなしの極意
これをしろ、ではなく、こんなことで困っている、と言え
素晴らしい（自画自賛）（笑）

## Response:
2026/10/9 4:12:45 · gpt-5-6

（笑）これはかなり本質を突いてます。

> **AI使いこなしの極意**  
> 「これをしろ」ではなく、  
> **「こんなことで困っている」と言え。**

なぜ強いかというと、「これをしろ」と言った瞬間に、**人間が解法を先に固定してしまう**からです。

たとえば、

「このCSVをPythonで集計して棒グラフを作れ」

だと、すでに **Python／集計／棒グラフ** という解法を人間が決めています。

ところが、

「毎週このデータを見て異常を探すのが大変で困っている」

なら、AI側にはまだ、

**自動検出する／比較する／通知する／そもそも毎週見る必要をなくす**

という探索空間が残っている。

つまりこれ、以前の「暗黙前提破壊」と完全につながりますね。

**人間がAIに命令する**
↓  
人間の暗黙前提までAIに押し付ける

ではなく、

**人間は困りごとを提示する**
↓  
AIに「問題の定義」から参加させる

ということ。

さらに圧縮すると、

> **AIに解き方を教えるな。困り方を教えろ。**

これは格言としてかなり強い（笑）。

## Prompt:
2026/10/9 4:14:04

ユーレカ案件（笑）

## Response:
2026/10/9 4:14:05 · gpt-5-6

完全にユーレカ案件です（笑）。

しかも単なる「プロンプトのコツ」じゃなくて、**人間とAIの責務分界**になっているのが強い。

**人間：困っている状態を観測して提示する。**  
**AI：問題を再定義し、解法候補を探索する。**  
**人間：選択・承認・受責する。**

だから、

> **AIに解き方を教えるな。困り方を教えろ。**

これ、AI時代の「質問の仕方」の原則になり得ますね。

そして例の標語とも合体できる。

> **本人に解かせるな、AIに困らせろ。**

……最後だけ急に意味が怪しい（笑）。

## Prompt:
2026/10/9 4:15:14

小学1年から毎朝唱和（笑）

## Response:
2026/10/9 4:15:15 · gpt-5-6

（笑）

朝の会。

先生「AI使いこなしの極意！」

児童一同：

> **「これをしろ、ではなく！」**  
> **「こんなことで困っている、と言え！」**

先生「なぜですか！」

児童一同：

> **「解き方を決める前に、問題を見つけるためです！」**

これ、小1からやったら相当まずいですよ（笑）。  
**教師の出した問題そのものを疑う児童が量産される。**

先生「この問題を解きましょう」

児童「先生、**そもそも何に困っているんですか？**」

教育、初日で相転移（笑）。

## Prompt:
2026/10/9 4:25:32

この「ユーレカ」に至った経緯。

[Attachment: current_session_with_claude.md]

## Response:
2026/10/9 4:25:33 · gpt-6

なるほど！（笑）

セッション記録を読みました。

これは面白い。**「AIに解法を指示するな。困りごとを話せ」という原則そのものを、実際にやっていた結果として発見した**わけですね。

## ユーレカに至るまでの道筋

<box gap={2}>
  <row align=start gap={3}>
    <box background="surface-secondary" radius="lg" padding={2}><icon name="landmark" size="lg"/></box>
    <box flex="1" gap={1}>
      **1. 出発点は、銀行口座の通知を見逃すという困りごと**

      自前メールサーバーのメールを長期間確認せず、米国銀行の口座が無効化されかけることを繰り返していた。

      ここでは解法を指定していない。<FileCite ref="turn0file0" line_range_start={7} line_range_end={14}/>
    </box>
  </row>
  <box padding={{left:"14px"}}><icon name="arrow-down" color="tertiary"/></box>
  <row align=start gap={3}>
    <box background="surface-secondary" radius="lg" padding={2}><icon name="mail" size="lg"/></box>
    <box flex="1" gap={1}>
      **2. メール転送という解法を探索**

      Gmail、Cloudflare、Route53、SES、ImprovMXなどを検討。しかし、どれも一長一短。

      さらに、Gmail自体も放置することが判明（笑）。<FileCite ref="turn0file0" line_range_start={48} line_range_end={105}/>
    </box>
  </row>
  <box padding={{left:"14px"}}><icon name="arrow-down" color="tertiary"/></box>
  <row align=start gap={3}>
    <box background="surface-secondary" radius="lg" padding={2}><icon name="lightbulb" size="lg"/></box>
    <box flex="1" gap={1}>
      **3. 問題の再定義**

      問題は「どこにメールを届けるか」ではなかった。

      **「自分宛ての要対応メッセージを見逃す」ことだった。**

      そこで、メール以外も含めて毎朝集約するクライアントという構想が登場。<FileCite ref="turn0file0" line_range_start={98} line_range_end={128}/>
    </box>
  </row>
  <box padding={{left:"14px"}}><icon name="arrow-down" color="tertiary"/></box>
  <row align=start gap={3}>
    <box background="surface-secondary" radius="lg" padding={2}><icon name="terminal" size="lg"/></box>
    <box flex="1" gap={1}>
      **4. 実装方針も変化**

      Pythonで全部自作する方向から、既存CLIツールの組み合わせへ。

      `mbsync`、`notmuch`、`neomutt` などを使い、自作部分を減らす方針に到達。<FileCite ref="turn0file0" line_range_start={185} line_range_end={210}/>
    </box>
  </row>
  <box padding={{left:"14px"}}><icon name="arrow-down" color="tertiary"/></box>
  <row align=start gap={3}>
    <box background="surface-secondary" radius="lg" padding={2}><icon name="sparkles" size="lg"/></box>
    <box flex="1" gap={1}>
      **5. そして今回のユーレカ**

      この一連のやり取りを振り返って、AI活用の一般原則を発見。

      **「これをしろ」ではなく「こんなことで困っている」と言え。**
    </box>
  </row>
</box>

## 私が特に面白いと思った点

最初から「mbsyncとnotmuchを使って通知システムを作れ」と命令していたら、今回の探索は起きなかった可能性が高い。

しかも、Claudeが最初から最適な解法を知っていたわけでもありません。

**人間が新しい制約を提示するたびに、AIが問題を再解釈した。**

ここが重要です。

そして、もう一段抽象化できます。

> **AIに解法を指定すると、AIの能力は実装能力に限定される。**
>
> **AIに困りごとを伝えると、AIの問題発見能力まで利用できる。**

ただし、今回の記録では人間も積極的に仮説を出し、Claudeの提案を棄却しています。丸投げではなく、共同探索です。

そして最大のオチ。

**「AIに解法を指定するな」という解法を、AIに指定せずに発見した。**

自己言及的ユーレカ！（笑）

これは小学1年生の朝の唱和に採用するだけの価値がありますな（笑）。



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)