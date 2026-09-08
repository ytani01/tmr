# TODO-012 implementer report 2（reviewer 指摘の反映）

対象: `implementer-task2.md` の A〜D。

## A. 検証を `PomodoroConfig.__post_init__` にまとめる

- `src/tmr/pomodoro.py:1-27` — `PomodoroConfig` に `__post_init__` を追加。
  `work_sec` / `break_sec` / `long_break_sec` は
  `not math.isfinite(value) or value <= 0` で、`cycles` は `< 1` で
  それぞれ `ValueError`（フィールド名と値入りのメッセージ）。
- `src/tmr/pomodoro.py:29-32` — `phases()` を元のジェネレータに戻し、
  `_phases()` への分割は取り消した（`cycles` の検証は
  `PomodoroConfig` 側に移ったので不要）。
- `tests/test_pomodoro.py:11-42` — `phases()` の `ValueError` テストを、
  `PomodoroConfig(...)` 構築時の `ValueError` テストへ置き換え。
  `work_sec` / `break_sec` / `long_break_sec` それぞれに `0`・`-1`・
  `nan`・`inf`、`cycles` に `0`・`-1` を当てて確認（14 通り）。

## B. `nan` / `inf` も弾く

- `src/tmr/clock.py:7,24` — `math` を import し、`TimerClock.__init__` の
  検証を `not math.isfinite(t_limit) or t_limit <= 0` に拡張。
- `src/tmr/pomodoro.py` の `__post_init__`（A に同じ）でも同様に
  `math.isfinite()` を見る。
- `src/tmr/cli.py:4,17-23` — `_reject_non_finite(ctx, param, value)` を
  1 つ作り、`click.BadParameter` を上げる。`pomodoro` の `-w`/`-b`/`-l`
  の `callback=` に共通で指定（`FloatRange` の後段で効く）。`timer` の
  `minutes` と `-c` は `int` なので対象外（変更なし）。
- `tests/test_clock.py:24-30` — `TimerClock` の異常値テストを
  `parametrize` にし、`0`・`-1`・`nan`・`inf` をまとめて確認。
- `tests/test_cli.py:63-79` — `-w nan`/`-w inf`/`-b nan`/`-l inf` が
  終了コード 2、出力に `"must be finite"` を含むことを確認。

## C. CLI テストを強化する

- `tests/test_cli.py:40-79` — 既存の 0 値テストを `parametrize` にして
  負値（`-- -1`、`--cycles -1`、`--work-time -1`）を追加。
  すべて `"is not in the range" in result.output` も確認するよう変更。
  `nan`/`inf` 系は別メッセージ（`"must be finite"`）なのでそちらを確認
  （B 参照）。
- `timer` の負の引数は `runner.invoke(timer, ["--", minutes])` のように
  `--` を挟まないと `-1` がオプションと誤認されて別エラーになったため、
  そのように直した。

## D. `CLAUDE.md` に二重の防御を書く

- `CLAUDE.md`（「Timer は 3 つに分かれている」節、`AlarmParams` の説明の
  直後）に 2 行追加。CLI では `IntRange`/`FloatRange` とコールバックで、
  ライブラリ層では `TimerClock`/`PomodoroConfig` の `ValueError` で、
  それぞれ 0 以下・`nan`・`inf` を弾く二重の作りであることと、
  ライブラリとして直接使う経路が CLI を通らないためという理由を書いた。
  `（TODO-012）` を付けた。

## 検証結果

- `uv run pytest tests -q` — 125 passed
- `uv run ruff format --line-length 78 src tests` — 24 files left unchanged
- `uv run ruff check --fix --extend-select I src tests` — All checks passed!
- `uv run basedpyright src tests` — 0 errors, 0 warnings, 0 notes
- `uv run mypy src tests` — Success: no issues found in 24 source files
- `uv run tmr pomodoro -w 0.1 -b 0.1 -l 0.1 -c 2` — 実行し、WORK フェーズが
  正常に進むこと（エラーにならないこと）を確認（`q` で途中終了）。
- `COLUMNS=80 uv run tmr pomodoro --help` の出力を実行前後で比較し、
  変化が無いことを確認（`README.md` は変更不要）。
- 行長: `awk` はバイト数を数えて日本語行を過大に報告したため、
  Python の `len()`（文字数）で 78 文字超えの行が無いことを確認済み。
- 手動確認: `tmr pomodoro -w nan` / `-w inf` / `-b nan` / `-l inf` が
  いずれも exit 2 で `must be finite: ...` を出すことを確認。

## 判断が要る点・残る懸念

- 特に判断が要る点は無し。A〜D はすべて完了。
- 範囲外（今回は手を入れていない）: reviewer 報告の 3（`t_limit` を
  `__init__` 後に代入されたときの防御）は、依頼どおり TODO-013 に残す。
