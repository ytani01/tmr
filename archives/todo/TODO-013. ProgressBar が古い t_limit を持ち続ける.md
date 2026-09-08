# TODO-013. `ProgressBar` が古い `t_limit` を持ち続ける

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5 / effort medium | reviewer + verifier |
| 実施 | Opus 5 / effort high | reviewer + verifier |

| 担当 | モデル | effort | output | cache_creation | 料金の割合 |
|------|--------|--------|--------|----------------|-----------|
| main | Opus 5 | high | 12,656 | 68,144 | 76% |
| verifier | Sonnet 5 | 記載なし | 2,321 | 43,076 | 12% |
| reviewer | Sonnet 5 | high | 2,439 | 45,361 | 12% |
| 合計 |  |  | 17,416 | 156,581 | 概算 $2.2 |

- 見込みの担当は、立てたときは `implementer + reviewer + verifier` だった。
  着手して差分の見当がついた時点で、3 ファイル・20 行程度と分かったので、
  **実装を main が持つ形に見込みの行を書き直してから着手した**
  （`~/.claude/CLAUDE.md` の「立てたときと着手するときで見立てが違って
  いたら、着手時に見込みの行を書き直してよい」）
- verifier は定義のモデルが haiku。実装の意図どおりかの判断と、
  追加したテストが意味を持つかの確認が要るので Sonnet 5 に上書きした。
  定義に `effort` の行が無い（haiku 前提のため）
- reviewer は定義のまま（sonnet / effort high）。分岐の置き換えが
  2 箇所だけで範囲が狭いので上書きしなかった
- 立てたのは TODO-010 のコミットと同じ回（`a40cc83`）で、着手まで
  空いたため、集計は `--since '2026-09-08 11:49:51'`（TODO-012 の
  決着コミットの時刻）で切った

## きっかけ

TODO-010 の reviewer が指摘した。`TimerView.display()` は毎回
`clock.t_limit` を読むのに、`ProgressBar` は `__init__` 時点の `total` を
持ったままなので、両者が食い違うとプログレスバーの目盛りだけが古い値で
描かれる。

`Timer.__init__` が `TimerClock` と `TimerView` へ同じ値を渡すだけなので
実害は出ていなかったが、`tests/test_view.py` が `clock.t_limit` を後から
書き換えていて、**テストの中では既にずれた状態を作っていた**
（`ProgressBar` がモックなので露見していなかった）。

## やったこと

**`ProgressBar` から `total` を状態として持たせるのをやめ、
`get_str()` / `display()` の引数にした。** 値が 2 箇所に残る形
（`__init__` の値を引数で上書きする）は、食い違いを無くすという趣旨に
合わないので採らなかった。

- `src/tmr/progress_bar.py` — `__init__` から `total` を削除
  （`bar_length` が第 1 引数になった）。
  `get_str(val, total, *, bar_len, stop)` /
  `display(val, total, ...)` へ変更。`total` は `val` と対になる必須値
  なので、位置引数のままにした
- `src/tmr/view.py` — `TimerView.__init__(term, title)` から `t_limit` を
  落とし、`display()` の中で `clock.t_limit` を毎回 `get_str()` へ渡す
- `src/tmr/timer.py` — `TimerView(...)` の呼び出しを追随
- テスト — 呼び出し側を追随したうえで、
  `test_get_str_total_not_kept`（同じ `val` で `total` だけ変えると
  出力が変わる）と `test_pbar_uses_current_t_limit`（`clock.t_limit` を
  書き換えると新しい値が `ProgressBar` へ渡る）を 1 件ずつ足した

## 確かめたこと

- `uv run pytest tests` — 148 件全通過
- lint 4 つ（`ruff format` / `ruff check` / `basedpyright` / `mypy`）—
  すべて通過。追加の整形なし
- 古い API（`ProgressBar.total`、3 引数の `TimerView(...)`）が
  `src` / `tests` / `docs` / `README.md` に残っていないこと
- 疑似端末での実動 — `uv run tmr timer 1` でバーが伸び残り時間が減ること、
  `uv run tmr pomodoro -w 0.1 -b 0.1 -c 2` で WORK フェーズの進捗率が
  `0.0%` から単調に増えることを確認
- 追加した 2 件のテストが、変更前のコードでは落ちること
  （`git stash` で src 側だけ戻して確認）

## 残ること

追加した 2 件のテストは、変更前のコードに対しては API のシグネチャ違いの
`TypeError` で落ちる。**「値の食い違い」そのものを再現して落とす形には
できていない**（本番コードには実行中に `t_limit` を書き換える経路が無く、
再現条件を作れない）。`t_limit` を変える機能（実行中の延長など）を足す
なら、そのときに食い違いを直接突くテストを書けるようになる。

## 分担の振り返り

- **reviewer** — 要修正 0 件。分岐 2 箇所（`rate = val / total ...` と
  `if val >= total or stop:`）の意味が変わっていないことと、
  `total` が `nan` / `inf` の経路が `TimerClock.__init__` の検査で
  塞がれていることを確かめた。追加した 2 件のテストが
  「`TimerView` が最新の値を渡す」「`ProgressBar` が渡された値を使う」の
  両側を分担して見ている、という評価もここで出た
- **verifier** — テストと lint に加えて、`git stash` で src 側だけ
  変更前に戻し、**追加したテストが本当に落ちるか**を確かめた。
  そこで「落ちる理由がシグネチャ違いであって、値の食い違いではない」
  という限界を見つけた。これは「残ること」に書いた。依頼文に書いた
  `uv run tmr timer 0.1` が `click.IntRange` に弾かれる
  （`MINUTES` は整数）ことも報告してきた — 依頼文の誤り
- **見込みとの食い違い** — 立てたときは implementer を入れていたが、
  着手して差分の見当がついた時点で外した。結果として 20 行程度の変更に
  収まり、main が実装しても reviewer と verifier が別に見ているので
  質は落ちなかった。$2.2 は TODO-012（$14.3）の 6 分の 1
- **次に同じ規模の項目をやるなら** — 「API のシグネチャを変えて
  呼び出し側を追随させるだけ」の項目では implementer を立てない。
  差分が小さいほど、依頼文を書いて報告を読む往復のほうが高くつく。
  一方 **verifier のモデル上書き（haiku → sonnet）は残す**。
  今回いちばん価値があった指摘（テストが落ちる理由の限界）は、
  手順をなぞるだけでは出てこないもので、`git stash` で変更前に戻して
  確かめるところまで自分で組み立てた結果だった。
  reviewer は sonnet のままでよかった（分岐 2 箇所を見るだけ）
