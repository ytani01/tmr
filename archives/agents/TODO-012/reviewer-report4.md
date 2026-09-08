# TODO-012 reviewer report 4（追加分の確認・打ち止め）

対象: `implementer-report4.md` の I〜K。依頼の 7 点だけを見た。
（`getattr` の共通化は「触らない」と決まったので見ていない。
`t_limit` の後からの代入は TODO-013。）

**指摘は無い。要修正 0 件、検討 0 件。**
7 点すべて、意図どおりであることを実測で確認した。
最後に、対応不要の小さな気づきを 1 つだけ書いた。

## 1. `timefmt.py` の `HOUR_DAY` / `SEC_DAY`

問題無い。

- `src/tmr/timefmt.py:6-9` — `SEC_MIN = 60  # seconds per minute` /
  `MIN_HOUR = 60  # minutes per hour` に対し、
  `HOUR_DAY = 24  # hours per day` /
  `SEC_DAY = SEC_MIN * MIN_HOUR * HOUR_DAY  # seconds per day`。
  「小さい単位_大きい単位 ＝ 大きい単位あたりの個数」という既存の
  命名とコメントの形にそのまま乗っている。
- 生の `86400` を書かず単位定数から組み立てているので、
  `CLAUDE.md` の「時間の単位は `timefmt.py` にある」という記述とも合う。
- 置き場所も `t_str()` の前、既存 2 定数の直後で自然。

## 2. `AlarmParams.__post_init__` の境界の向き

問題無い。上限ちょうどは通り、超えると弾く（実測）。

- `src/tmr/timer.py:38` — `value < 0 or value > MAX_ALARM_SEC` なので
  **`MAX_ALARM_SEC` は含む**。
- 実測: `AlarmParams(0, 86400, 86400)` は通る。
  `AlarmParams(0, 86401, 1.5)` は
  `sec1 must be a finite number in [0, 86400]: sec1=86401`。
  `-0.0001` / `inf` / `nan` も同じメッセージで `ValueError`。
- `count` は `< 0` のみ（上限無し）。実測で `AlarmParams(10**9, ...)` は
  通る。`count` は `range()` に渡るだけで `time.sleep()` には渡らない
  ので、上限を付けないのは筋が通っている。
- メッセージが `in [0, 86400]` と閉区間で書かれており、境界が読み取れる。

## 3. `cli.py` の `FloatRange(min=0, max=SEC_DAY)`

問題無い。向きは 2 と一致し、**`--alarm-count` に上限は付いていない**。

- `src/tmr/cli.py:72,82` — `click.FloatRange(min=0, max=SEC_DAY)`。
  `max_open` は付いていないので上限を含む。実測で
  `--alarm-sec1 86400` は exit 0、`--alarm-sec2 86401` は
  `86401.0 is not in the range 0<=x<=86400.` で exit 2。
- `src/tmr/cli.py:64` — `--alarm-count` は `click.IntRange(min=0)` の
  ままで `max` は無い。実測で `--alarm-count 99999999` は exit 0 で
  `AlarmParams(count=99999999, ...)` が渡る（`Timer` をモックして確認）。
- `min` 側も 0 を含んだまま。実測で
  `--alarm-count 0 --alarm-sec1 0 --alarm-sec2 0` は exit 0 で
  `AlarmParams(count=0, sec1=0.0, sec2=0.0)` が渡る。

## 4. 期待値を `"must be finite"` → `"is not in the range"` に変えた件

妥当。実際の挙動と一致している（実測）。

- `--alarm-sec2 inf` は
  `Error: Invalid value for '--alarm-sec2' / '--s2': inf is not in the
  range 0<=x<=86400.`。`max` が付いたことで `FloatRange` の段で弾かれ、
  コールバックまで届かないので、テストの期待値の変更は正しい。
- **`nan` は今もコールバックで弾かれている。** 実測で
  `--alarm-sec1 nan` / `--alarm-sec2 nan` はどちらも
  `must be finite: nan`（`nan` は比較がすべて False になり範囲チェックを
  素通りするため）。`tests/test_cli.py` の
  `test_timer_alarm_sec1_nan_rejected` がこの経路を押さえている。
- 上限の無い `-w` / `-b` / `-l` では `inf` も今までどおりコールバックで
  弾かれる（実測: `-w inf` → `must be finite: inf`）。
  `tests/test_cli.py` の `test_pomodoro_non_finite_rejected` が
  `inf` と `nan` の両方を見ているので、**コールバックが素通しになる
  退行はテストで捕まる。**

## 5. `CLAUDE.md` の追記

事実として正しく、簡潔。問題無い。

- `CLAUDE.md:54-60` の 3 つの主張はいずれも実装と一致する。
  - `TimerClock` / `PomodoroConfig` / `AlarmParams` の 3 か所で
    `ValueError` を上げている（各ファイルで確認）
  - 「アラームの回数と間隔は 0 を許す（鳴らさない／間を空けない）」—
    実測で 0 が通る。`count=0` は `thr_alarm()` の `range(0)` で
    1 度も鳴らないので説明も正しい
  - 「間隔は `time.sleep()` が `OverflowError` にならないよう 1 日
    （`timefmt.SEC_DAY`）を上限とする」— 報告 3 で実測した
    `OverflowError` を避けるための保守的な上限で、理由の書き方も妥当
- 文体（名詞止め・である調）と強調の使い方は既存の箇条書きと揃っている。
  7 行あるが重複や言い換えは無い。行長も 78 文字以内。

## 6. `README.md` の help

一致している。

- `COLUMNS=80` で `tmr timer --help` / `tmr pomodoro --help` を取り直し、
  `README.md` の該当ブロックと `diff` して**差分なし**。
  ついでに `tmr --help`（グループ）のブロックも差分なし。
- `--alarm-sec1` / `--alarm-sec2` の
  `[default: 0.5; 0<=x<=86400]` まで実出力どおり。

## 7. 前回までに確認した点

崩れていない。

- 設定ファイル経由でも新しい上限が効く（`XDG_CONFIG_HOME` を差し替えて
  実測）。`[timer] alarm-sec2 = 86401` は
  `Invalid value for '--alarm-sec2' / '--s2': 86401.0 is not in the
  range 0<=x<=86400.` で exit 2。`alarm-count = 0` /
  `alarm-sec1 = 0` は exit 0 で `AlarmParams(count=0, sec1=0.0, ...)`。
- `PomodoroConfig` の frozen、`phases()` の無限ループが塞がれたこと、
  時間・サイクル数の 0 / 負値 / `nan` / `inf` の拒否、
  小さい正の小数（`-w 0.1`）が通ること、`Timer.__init__` の順序、
  `ProgressBar` のゼロ除算ガードは、いずれも変更されていない。
- タイマー本体（`minutes`、`-w` / `-b` / `-l`）に上限を足していないのは
  依頼どおりで、意図した範囲に収まっている。
- 追試: `pytest tests` 146 passed / `ruff format --check`（24 files
  already formatted）/ `ruff check` All checks passed /
  `basedpyright` 0 errors / `mypy` Success。
- 行長: `git diff` の追加行に 78 文字超えは無い
  （`timer.py:38` の条件式は 78 文字ちょうど）。
  `src/tmr/timer.py:62` と `CLAUDE.md:3,178,179` は今回より前からある行。
- 指示範囲外の変更は混ざっていない。

## 対応不要の気づき（打ち止めの妨げにはならない）

- `tests/test_cli.py` の `test_timer_alarm_sec_max_allowed` は exit 0 と
  `main()` の呼び出しだけを見ており、`test_timer_alarm_zero_allowed` の
  ように渡った `AlarmParams` の値までは見ていない。上限ちょうどの値は
  `tests/test_timer.py` の `test_alarm_params_sec_max_allowed` が
  `AlarmParams` 側で確かめているので、穴は無い。**直す必要は無い。**
