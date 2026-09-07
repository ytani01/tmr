# TODO-010. `Timer` を分割し、引数をデータクラスにする

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5 / effort high | implementer + reviewer + verifier |
| 実施 | Opus 5 / effort medium | implementer + reviewer + verifier |

| 担当 | モデル | effort | output | cache_creation | 料金の割合 |
|------|--------|--------|--------|----------------|-----------|
| main | Opus 5 | medium | 28,153 | 81,581 | 47% |
| implementer | Opus 5 | medium | 23,349 | 82,169 | 27% |
| reviewer | Opus 5 | high | 7,962 | 92,095 | 18% |
| verifier | Sonnet 5 | 記載なし | 756 | 129,329 | 8% |
| 合計 |  |  | 60,220 | 385,174 | 概算 $6.9 |

- implementer は定義のモデルが sonnet。5 ファイルにまたがる書き換えで
  判断が多く残るので Opus 5 に上書きした
- verifier は定義のモデルが haiku。チェック項目を 1 つずつ実装に当てる
  必要があるので Sonnet 5 に上書きした。定義に `effort` の行が無い
- 集計は `--since '2026-09-08 03:17:38'`（TODO-008・TODO-009 と同じ
  コミットで立てたため、着手時刻で範囲を切った）

## きっかけ

`src/tmr/timer.py` が 516 行あり、経過時間の計算・画面表示・キー操作・
アラームがすべて 1 つのクラスに入っていた。TODO-009（モジュール構成の
整理）が済んで、次は中身を分ける番だった。

引数の `title: tuple[str, str]` と
`alarm_params: tuple[int, float, float]` も、位置でしか意味が分からない
形のままだった。

## やったこと

### 分割

- `src/tmr/clock.py` の `TimerClock` — 経過時間、ポーズ、早送り・
  巻き戻し。端末に触らないので単体で試せる。式は分割前の `main()` /
  `fn_forward()` / `fn_backward()` からそのまま移した
- `src/tmr/view.py` の `TimerView` — 列の定義、幅に応じた省略、
  スタイル付け。`PERCENT_COLOR` / `PBAR_LEN_MIN` / `STAT_STR_*` も移した
- `src/tmr/timer.py` の `Timer` — メインループとキー操作・アラームだけの
  層になった。`Terminal` を作り、`TimerClock` と `TimerView` を持つ

`Timer` には `t_start` / `t_elapsed` / `is_paused` を残していない
（`timer.clock.elapsed` のように参照する）。

### 表示順と削除の優先順位を 1 箇所に

分割前は `col_list()` の挿入順（表示順）と `COL_PRIORITY`（削る順）の
二重管理で、片方だけ直すと崩れた。`TimerCol` に `priority` を持たせ、
**`col_list()` の並びが表示順、`priority` の小さいものから削る**形にした。

### データクラス

- `TimerTitle(text, color, width)` — `width` が正なら表示時に桁を揃える
- `AlarmParams(count, sec1, sec2)`
- `type AlarmParams = tuple[int, float, float]` の別名は消した

### ジェネレータ

`PomodoroTimer.run()` からフェーズの並びを `phases(config)` に分けた。
桁揃え `f"{tt:16s}"` は `TimerTitle.width` へ移した。

### 後始末（reviewer の指摘を受けて）

- どこからも読まれない属性（`Timer.t_limit` / `Timer.title` /
  `TimerView.title`）を消した。分割前は `timer.t_limit = X` に意味が
  あったので、残すと黙って効かない属性になる
- `main()` で 3 回繰り返していた表示の呼び出しを `_display()` にまとめた

## 確かめたこと

- `uv run pytest tests -q` → 97 passed（分割前は 74）
- `uv run ruff format --line-length 78 src tests` → 差分なし
- `uv run ruff check --extend-select I src tests` → All checks passed!
- `uv run basedpyright src tests` → 0 errors
- `uv run mypy src tests` → Success
- 疑似端末（`script -qec "stty rows 24 cols 100; ..."`）で
  `tmr pomodoro` を動かし、フェーズ名が 16 桁で揃うこと、項目の並び、
  経過率による色の変化、アラームが鳴ることを見た

reviewer が、分割前の `Timer.display()` と `TimerView.display()` を
**総当たりで突き合わせた**（端末幅 0〜129 × `t_limit` 2 通り × 経過率
6 通り × ポーズ・実行中・アラームの全組み合わせ、12480 ケース）。
`click.echo` / `click.secho` の呼び出し、各列の `use` / `value` /
`color`、`ProgressBar.get_str()` に渡る `bar_len` と `stop` を比べて
**差分 0**。分割前のテスト 21 ケースが新しい構成のどこかに残っていることも
確かめた。

## 残ること

reviewer が挙げた残りは、別項目にした。

- TODO-012 — `tmr timer 0` のゼロ除算、`tmr pomodoro -c 0` で固まる
- TODO-013 — `ProgressBar` が古い `t_limit` を持ち続け、`clock` 側と
  食い違い得る
- TODO-014 — `pomodoro.py` のログ漏れ、点滅表示のテストが無い

`TimerView.display()` の `sorted()` を毎周回作っている点は、9 要素で
0.2 秒に 1 回なので直していない。

## 分担の振り返り

- **レビューを分けた効果が、いちばんはっきり出た項目。** reviewer は
  分割前の `timer.py` を `git show` で取り出して動かし、新旧の
  `display()` を総当たりで突き合わせた。テストが通ることを見ても
  「表示が 1 文字も変わっていない」は言えないので、これは verifier の
  仕事では出てこない。読まれない属性が残っている件も、
  「分割前は意味があった」まで遡って初めて危険だと分かる指摘だった
- 実装を分けた判断も合っていた。設計を `instructions.md` に書き切って
  なお、implementer は 4 点を設計から外す判断をしており
  （`start()` での `is_paused` 解除、`TimerTitle.display_text`、
  省略ループの形、`Timer.display()` を残さない）、どれも妥当だった。
  設計文書だけでは決めきれない粒度が残ると分かった
- **依頼文に `CLAUDE.md` の更新を入れたのは間違いだった。** 実装担当は
  `CLAUDE.md` を触らない決まりなので、そこだけ宙に浮いた（main が
  引き取った）。次からは文書の担当を最初から分けて書く
- 見込みは effort high だったが、設計を先に固めたぶん main は medium で
  足りた。次に同じ規模なら、同じ 3 担当で、`CLAUDE.md` の更新だけ
  main の作業として依頼文の外に出す
