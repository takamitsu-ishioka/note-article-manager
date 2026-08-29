# DB更新作業を自動化するな。DB更新作業を消せ

## よくある光景

開発チームで、こんなやり取りが発生する。

> データベースに列を追加する作業があります。  
> データベースが古いままだとエラーが起こるので、バージョンアップ用スクリプトを実行してください。

そして手順書が作られる。

しばらくすると、

> 結構ややこしいことをやらねばいけないのですね。

> 誰かこれをやって、うまくいった人はいませんか？

さらにコード変更が進む。

> これをやらないとエラーが出ることに今気づいた。

> あれ、エラー出ます？

> あ、出るわ。

そして最終的に、

> 最新developをpullした人は早めに実施してください。

となる。

誰かがサボったわけではない。

DB変更に備えてスクリプトを作り、手順書を書き、事前に周知し、動作確認まで依頼している。

むしろ、かなり真面目に対策している。

それでも問題が起きる。

ならば、人ではなく設計を疑ったほうがいい。

---

## 何が起きているのか

状態を単純化するとこうなる。

```text
Git repository
  ├── source code ───────── version N+1
  └── migration script ──── version N+1

Developer environment
  └── local database ────── version N
```

開発者が最新コードを取得する。

```bash
git fetch origin
git merge origin/develop
```

すると、

```text
source code = N+1
database    = N
```

という「段差」が生まれる。

この段差を埋めるために、

- Teamsで周知する
- 手順書を読む
- migration scriptを実行する
- 成功したか確認する
- 忘れた人に再度知らせる

という人間の作業が必要になる。

私は以前から、

> **バグは段差に湧く**

と考えている。

この場合、その段差を **人間の注意力で埋めようとしている** こと自体が問題なのである。

---

## migration scriptをGitに入れれば解決するのか

しない。

migration scriptがGit repositoryに存在していても、

> 「最新コードを取得した人は、この手順を実行してください」

と言っているなら、依然として人間が整合性維持機構の一部になっている。

必要なのは単にSQLファイルをGit管理することではない。

より正確には、

> **あるrevisionのソースコードを取得すれば、そのrevisionが要求するDBの構造・初期状態・migration履歴を同じバージョン空間から再現できること**

である。

DBファイルそのものをGitにcommitする必要はない。

schema、migration、seedなど、DBを再構築するための一次情報がrepositoryに存在すればよい。

---

## ローカルDBはbuild artifactである

ここまで整理すると、ローカル開発DBの位置づけが変わる。

ローカルDBは、人間が大切に維持管理する開発資産ではない。

**repositoryにある一次情報から生成されるbuild artifact(中間生成物)である。**

```text
repository
├── source code
├── DB schema / migrations / seed
└── build definition
        │
        ▼
     make build
        │
        ├── application
        └── local database
```

したがって開発者の操作は、たとえばこれだけでよい。

```bash
git fetch origin
git merge origin/develop
make build
```

すると機械が勝手に、

```text
building application ...
done

building local database from ./sqls/initialize.sql ...
done
```

と処理する。

DB schemaが変更されていれば、

```text
schema changed
rebuilding local database ...
done
```

となる。

開発者はDB変更の存在すら知らなくてよい。

極端に言えば、

> 知らんがな。

でよいのである。

---

## SSoTは何か

この問題を考えるとき、最初に決めるべきなのは操作手順ではない。

次の4点である。

### 目的

現在のrevisionが要求する開発環境を再現する。

### 入力

Git repositoryに保存された一次情報をSSoTとする。

### 交換形式

SQL、migration definition、schema definition、seed dataなど、サブシステム間で必要となる再現可能な形式を使う。

### 出力

現在のrevisionと整合したapplicationとlocal database。

このように考えると、ローカルDBは入力ではなく出力であることが分かる。

そして、出力を人間が手作業でSSoTに追従させる必要もなくなる。

---

## 「DB更新を楽にする」は目的ではない

問題を、

> DB更新作業が面倒だ。

と認識すると、

> migration scriptを作ろう。  
> 手順書を書こう。  
> 自動化スクリプトを作ろう。  
> Teamsで通知しよう。

という改善策が出てくる。

しかし、もう一段上から見ると問いそのものが変わる。

> **なぜ開発者がDB更新という作業をしなければならないのか？**

最新revisionを取得した以上、そのrevisionが要求する環境を構築する責任はbuild systemに持たせればよい。

すると目標は、

> ❌ DB更新作業を効率化する

ではなく、

> ⭕ DB更新作業という行為そのものを消す

になる。

---

## 人間を整合性維持機構にしない

人間に、

> 「Aを変更したらBも変更すること」

と要求する設計は弱い。

AとBの対応関係を機械が知っているなら、機械にやらせればよい。

```text
変更
 ↓
依存関係を機械が検出
 ↓
必要な派生物を再生成
 ↓
整合した状態
```

これなら「忘れる」という故障モード自体が存在しない。

注意喚起を強化する必要もない。

チェックリストを増やす必要もない。

教育を徹底する必要もない。

人間が頑張らなくても正しい状態になる。

---

## まとめ

DB変更に伴って、

- 手順書を書く
- Teamsで周知する
- 各開発者がmigrationを実行する
- 実行したか確認する
- 忘れた人に再度知らせる

という作業が発生しているなら、個々の作業を効率化する前に設計を疑ったほうがよい。

理想は、

```bash
git fetch origin
git merge origin/develop
make build
```

だけである。

そして、

```text
building local database from SSoT ...
done
```

となる。

**人間がやっている付随作業を自動化するのではない。**

**その付随作業が存在しない世界を設計する。**

それが、この問題に対する最も単純な解決である。

---

## 次回

[これが「クリティカルシンキング」だ！](https://note.com/kisaburo_y/n/nd47c8a6f8c92)​​  


---

#データベース #DB #マイグレーション #ソフトウェア設計 #自動化 #SSoT #ビルド #開発環境 #問題解決 #生成AI

