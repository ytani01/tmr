# TODO-015. `README.md` と `docs/User.md`, `docs/Developer.md` を整備

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5 / effort high | implementer + verifier |
| 実施 | Opus 5 / effort high | implementer + verifier + wording |

| 担当 | モデル | effort | output | cache_creation | 料金の割合 |
|------|--------|--------|--------|----------------|-----------|
| main | Opus 5 | high | 21,470 | 175,280 | 58% |
| implementer | Opus 5 | medium | 17,557 | 76,468 | 28% |
| verifier | Sonnet 5 | 記載なし | 2,908 | 74,334 | 11% |
| wording | Haiku 4.5 | 記載なし | 6,087 | 41,799 | 2% |
| 合計 |  |  | 48,022 | 367,881 | 概算 $5.5 |

- implementer は定義のモデルが `sonnet`。3 文書にまたがる執筆で日本語の質が
  効くので Opus 5 に上書きした。`effort` は定義の `medium` のまま
- verifier は定義のモデルが `haiku`。表示例を自分で再現して桁まで突き合わせる
  必要があったので Sonnet 5 に上書きした。定義に `effort` の行が無い
- wording は定義のまま（Haiku 4.5）。定義に `effort` の行が無い
  （**Haiku は `effort` に対応しない**）
- 集計は `--since '2026-09-08 13:19:00'` で切った。TODO-015 を立てたあとに
  TODO-012 〜 014 を先に片付けたため、コミットで切ると他項目が混ざる

分担の理由と各担当の報告は
[archives/agents/TODO-015/](../agents/TODO-015/) にある。

## きっかけ

`README.md` に全部が入っていた。紹介、インストール、キー操作の一覧、
3 つの help 出力、設定ファイルの説明が 1 ファイルに並び、
初めて見る人にも、使い込む人にも、手を入れる人にも中途半端だった。

内部構造の説明は `CLAUDE.md` にしか無く、人間向けの入口が無かった。

図が 1 枚（`docs/fig1.png`）だけで、ポモドーロのフェーズの進み方も、
画面の項目の意味も、クラスの分かれ方も、文章でしか説明していなかった。

## やったこと

### 3 文書に分けた

| 文書 | 読み手 | 書くこと |
|---|---|---|
| `README.md` | 初めて見る人 | 紹介、特徴、インストール、最小の使用例、2 文書への導線 |
| `docs/User.md` | 使う人 | 全オプション、キー操作、画面の見方、幅による省略、アラーム、設定ファイル |
| `docs/Developer.md` | 手を入れる人 | モジュール構成、設計の意図、フェーズ制御、ログの規約、テスト、開発コマンド |

`README.md` にあった「COMMAND LIST」「3 つの help 出力」「設定ファイル」の
節は `docs/User.md` へ移し、`README.md` には残していない。
`README.md` は 146 行から 87 行になった。

`CLAUDE.md` とは役割で分けた。`CLAUDE.md` は Claude 向けの規約、
`docs/Developer.md` は人間向けの構造説明。

### 図を 6 枚入れた

mermaid を基本にし、画面の並びだけ枠線付きのテキスト図にした。

| 文書 | 図 | 形式 |
|---|---|---|
| `README.md` | ポモドーロのサイクル（作業 → 休憩 → 長い休憩 → 繰り返す） | mermaid |
| `docs/User.md` | 画面の各項目の位置と意味 | テキスト図 |
| `docs/User.md` | 幅を狭めたときに落ちていく様子（7 段階） | テキスト図 |
| `docs/Developer.md` | クラス構成 | mermaid |
| `docs/Developer.md` | `main()` のループの状態遷移と、戻り値によるフェーズ制御 | mermaid 2 枚 |
| `docs/Developer.md` | `col_list()` から表示が決まる流れ | mermaid |

### 誤った説明を直した

`README.md` に「ポモドーロタイマーでは、quit すると次のフェーズに移ります。
ポモドーロタイマーを終了する場合は、強制終了してください」とあったが、
実装と逆だった。

- `[N]` / `[ENTER]`（next）が次のフェーズへ進む。`enable_next=True` の
  ポモドーロでだけ有効
- `[Q]` / `[ESC]`（quit）はポモドーロ全体を終わらせる。強制終了は要らない

あわせて、`phases()` がフェーズを無限に返すこと、`-c` は「長い休憩までの
作業回数」であって全体の回数ではないことも `docs/User.md` に明記した。

### 見出しの書式

implementer が `## == ` の接頭辞を外していたが、従来の書式を保つことにし、
3 文書とも `## == ` / `### === ` に戻した。

## 確かめたこと

verifier が確認し、**直すべき指摘・直した方がよい指摘はどちらも 0 件**だった。

- `docs/User.md` の help 出力 3 種と COMMAND LIST を再取得し、1 文字一致
- 画面の実例（枠内 1 行と、幅 70/50/40/30/25/15/10 の 7 行）を、
  `Terminal` を `MagicMock` にして `TimerView.display()` を直接呼ぶ形で
  独自に再現し、桁と指示線の位置まで一致
- mermaid 5 枚を `@mermaid-js/mermaid-cli` でレンダリングし、
  エラー図になっていないことを確認
  （arm では同梱の chrome-headless-shell が動かないので、
  `-p '{"executablePath":"/usr/bin/chromium","args":["--no-sandbox"]}'` が要る）
- 落とす順、色の閾値（80% / 95%）、色が変わる列、アラームの仕様、
  早送り・巻き戻しの上下限、ポモドーロの制御を実装と突き合わせ
- `docs/Developer.md` のテストの patch 先の表を実際のテストと突き合わせ
- リンク 5 本がすべて実在
- `uv run pytest tests` → 150 passed、lint 4 本を流して `src` / `tests` に
  差分が出ないことを確認

好みの指摘が 1 件あった。`docs/User.md` の「落ちる順」の表と
`docs/Developer.md` の「表示順・priority」の表が、どちらも
`col_list()` を扱っている。ただし切り口が違う（利用者向けは落ちる順だけ、
開発者向けは `priority` の値）ので、そのままにした。

その後 wording を通し、「題」と「タイトル」の揺れ、効いていない太字、
長すぎる一文を直した。`docs/Developer.md` に 1 箇所残った「題」は
main が直した。

## 分担の振り返り

**各担当が何を見つけたか**

- implementer — 図 1 のフェーズ名が実物と違うこと（`WORK 1/4` ではなく
  `WORK:1/4`）、main が設計した表示例の桁が実物と合っていないこと、
  `stateDiagram-v2` では `[*]` が予約されているので遷移ラベルに
  角括弧を書けないことを見つけ、すべて直してから報告した。
  範囲外だが `-c` の色名を CLI で検証していない点にも気づいた
- verifier — 指摘 0 件。**ただし「何も無い」を確かめるための作業が本体**で、
  help 出力の 1 文字一致と、表示例 7 行の独自再現がそれにあたる。
  main も implementer も自分で作った例を見直しただけなので、
  ここを分けた意味はあった
- wording — 「題」と「タイトル」の揺れを見つけた。ただし
  `docs/Developer.md` の 1 箇所を取りこぼした
- main — README の説明が実装と逆であることを、設計の段階で見つけた

**見込みと食い違ったのはなぜか**

- 担当は implementer + verifier の見込みに wording が 1 つ増えた。
  これは利用者が途中で明示的に依頼したもので、見立ての誤りではない
- implementer と verifier のモデルを両方とも上げた。文書だけの項目なので
  定義のまま（sonnet / haiku）で足りると見ていたが、
  実際には「3 文書にまたがる日本語の質」と「表示例を自力で再現する」の
  2 つがあり、どちらも定義のモデルでは不安があった。
  **「文書だけ＝軽い」という見立てが雑だった**
- 料金は main が 58% を占めた。設計（design.md）を細かく書いたためで、
  これは意図どおり。おかげで implementer が 1 回で通り、
  verifier の指摘が 0 件で済んでいる

**次に同じ規模の項目をやるなら**

- **図を含む文書の項目では、main が設計の段階で表示例を実測しておく。**
  今回 main は桁を目分量で書き、implementer が実測して直し、
  verifier がもう一度実測した。**同じ実測を 3 回やっている。**
  main が 1 回測って design.md に貼れば、implementer の手戻りが消え、
  verifier は突き合わせるだけで済む
- **verifier のモデルは Sonnet 5 のままでよい。** 料金は 11%（$0.6）で、
  独自再現までやらせてこの額なら安い。Haiku に落として取りこぼす方が高くつく
- **wording は verifier より前に通す。** 今回は verifier のあとに通したので、
  wording が本文を書き換えた分は誰も確認していない
  （main が目視で protected 部分の無事を確かめただけ）。
  順番を入れ替えれば verifier の確認が最終形に対して効く
- implementer は Opus 5 のままでよい。28%（$1.6）で 3 文書 638 行が
  1 回で通っている
