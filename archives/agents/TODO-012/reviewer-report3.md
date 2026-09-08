# TODO-012 reviewer report 3（最終レビュー）

対象: `implementer-report3.md` の E〜H にあたる追加分。
（報告 1 の指摘 3＝`t_limit` の後からの代入は TODO-013 へ回すと決まった
ので見ていない。）

**要修正: 1 件（`CLAUDE.md` の追随、1〜2 行）。検討: 2 件。
好みの範囲: 1 件。**

## 要修正

### 1. `CLAUDE.md` の 4 行が、アラームの検証に追随していない

- 場所: `CLAUDE.md:54-57`
- 何が: 追記された 4 行は「`TimerClock` / `PomodoroConfig` でも
  `ValueError` で弾く」と書いてあるだけで、今回足した
  `AlarmParams.__post_init__`（`src/tmr/timer.py:27-37`）に触れていない。
- なぜ問題か: **アラームだけ境界が違う**（`count` は `>= 0`、
  `sec1` / `sec2` は `>= 0` で 0 を許す。時間・サイクル数は `> 0` /
  `>= 1`）。今の書き方だと「0 以下は弾く」と読めるので、次に触る人が
  `--alarm-sec1 0` を弾く向きに「揃えて」しまいかねない。
  `CLAUDE.md` は設計の正なので、片方だけ更新された状態は避けたい。
  根拠は `cli.py:63,72,82`（`IntRange(min=0)` /
  `FloatRange(min=0)`）と `timer.py:27-37` を読んだ結果、および
  `FloatRange(min=0).convert("0")` が `0.0` を返す実測。
- どうすると: 4 行のうち「`TimerClock` / `PomodoroConfig`」に
  `AlarmParams` を足し、「ただしアラームの回数と間隔は 0 を許す
  （鳴らさない／間を空けない）」を 1 行足す。

## 検討

### 2. 極端に大きい有限値では、まだアラームスレッドが死ぬ（実測）

- 場所: `src/tmr/timer.py:27-37`（`AlarmParams.__post_init__`）、
  `src/tmr/timer.py:347`（`time.sleep(s)`）
- 何が: 検証は「有限かつ >= 0」なので `1e18` や `1e300` は通る。
  一方 `time.sleep(1e18)` は
  `OverflowError: timestamp out of range for platform time_t` になる
  （実測。`1e9` は例外にならず眠る）。`click.FloatRange(min=0)` も
  `1e300` を通す（実測）。`thr_alarm()` は daemon スレッドなので、
  例外で落ちると `alarm_active` が True のまま残る。
- なぜ: 「`time.sleep()` が `ValueError` を投げる値を過不足なく覆うか」
  という観点では、負値（`sleep length must be non-negative`）と
  `nan`（`Invalid value NaN`）は覆えているが、**`OverflowError` に
  なる巨大な有限値だけ覆えていない**。
- ただし: `--alarm-sec1 1e18` は現実には打たれないし、覆ったところで
  「30 年眠る」か「スレッドが死ぬ」かの違いしかない。**直さない判断も
  十分に妥当**。直すなら上限（例: `SEC_DAY` 相当）を足すことになる。
- 注: CLI からこの値を渡してスレッドを実際に落とすところまでは
  試していない（`FloatRange` が通ることと `sleep` が落ちることを
  個別に実測し、`thr_alarm()` のコードを読んで繋げた）。

### 3. 「0 を許す」ことを CLI 側で確かめるテストが片側だけ

- 場所: `tests/test_cli.py:126-135`
  （`test_timer_alarm_count_and_sec1_zero_allowed`）
- 何が: `--alarm-count 0` と `--alarm-sec1 0` は見ているが、
  `--alarm-sec2 0` は見ていない。また `Timer` をモックしているので
  exit 0 と `main()` の呼び出ししか確認しておらず、
  **どんな `AlarmParams` が渡ったか**は見ていない。
- なぜ: 境界を「0 は可」に決めたことが今回の肝なので、
  `MockTimer.call_args` から `AlarmParams(0, 0.0, ...)` を確かめると、
  向きを取り違えた変更（`min_open=True` を付ける等）を捕まえられる。
  ただし `AlarmParams` 自体は `tests/test_timer.py:29-33`
  （`test_alarm_params_zero_allowed`）で見ているので、穴は小さい。
- 補足（良い点）: このテストは `tmr.cli.Timer` だけをモックしていて
  `AlarmParams` は実物なので、`__post_init__` の 0 許容は実際に通って
  いる（見かけだけのテストではない）。

## 好みの範囲

- `src/tmr/timer.py:32` と `src/tmr/pomodoro.py:21` の
  `for name in (...)` + `getattr` は同じ形が 2 か所になった。
  今は 2 か所とも短いので共通化するほどではないが、3 つ目が出たら
  小さなヘルパにまとめる場面。今回は現状でよいと思う。

## 確認して問題が無かったこと（実測）

- **アラームの境界は依頼どおり 0 を許す**。`FloatRange(min=0)` に
  `min_open` は付いておらず（`cli.py:72,82`）、
  `FloatRange(min=0).convert("0")` は `0.0` を返し、`"-1"` は
  `-1.0 is not in the range x>=0.` で弾く。`IntRange(min=0)` も
  `"0"` を通し `"-1"` を弾く。**0 を弾いてはいない。**
- `AlarmParams.__post_init__` は frozen と両立している（自分では
  代入していない）。`AlarmParams` は `@dataclass(frozen=True)` のまま。
  `Timer.DEF_ALARM = AlarmParams(999, 0.5, 1.5)` はクラス定義時に
  評価されるが、正の値なので import 時に落ちない（テストが通ることで
  確認）。
- `PomodoroConfig` を frozen にしたことで壊れる経路は見当たらない。
  - `src` / `tests` に `dataclasses.replace()` / `asdict()` /
    `astuple()` の使用は無い（grep 実測）。フィールドへの代入も無い。
  - `eq=True` + `frozen=True` で `__hash__` が付くのは、
    それまで unhashable だったものが hashable になるだけで、
    既存の使い方（比較・属性の読み出し）に影響しない。
  - 報告 2 の指摘 1 で実測した「`config.cycles = 0` の後に
    `phases()` が固まる」経路は塞がった（`FrozenInstanceError`）。
- `# type: ignore[misc]` の使い方は妥当。frozen dataclass への代入を
  mypy が `[misc]` で報告するのを抑えるもので、
  `tests/test_terminal.py:25,41` に同種の書き方の前例がある。
  抑制のしすぎ（行全体を `# type: ignore` にする等）はしていない。
  basedpyright / mypy とも 0 件で、未使用の ignore も出ていない。
- 設定ファイル経由でもアラームの検証が効く（`XDG_CONFIG_HOME` を
  差し替えて実測）。
  - `[timer] alarm-sec1 = nan` →
    `Error: Invalid value for '--alarm-sec1' / '--s1': must be finite: nan`
  - `[timer] alarm-count = -1` →
    `Error: Invalid value for '--alarm-count': -1 is not in the range x>=0.`
- `README.md` の `timer --help` / `pomodoro --help` は、`COLUMNS=80` で
  取り直した実出力と**完全に一致**（両ブロックを diff、差分なし）。
- 例外メッセージは読める文になった。
  `t_limit must be a finite number > 0: t_limit=nan`、
  `work_sec must be a finite number > 0: ...`、
  `sec1 must be a finite number >= 0: ...`、
  `count must be >= 0: ...`。境界の向き（`>` と `>=`）が
  実装と一致している。
- 追加テストは分岐を突いている。CLI 側は exit code に加えて
  `is not in the range` / `must be finite` を見ており、範囲チェックと
  コールバックのどちらで落ちたかを区別できる。`AlarmParams` の
  パラメータ化は負値・`nan`・`inf` を 3 フィールドに散らして当てている。
- 前回・前々回に問題が無かった点は崩れていない。
  - 小さい正の小数は通る（`-w 0.1 -b 0.1 -l 0.1 -c 1` で exit 0、
    `PomodoroConfig(work_sec=6.0, ...)` が渡ることを前回実測。
    今回もテスト 138 件が通る）
  - 0 / 負値 / `nan` / `inf` の CLI 拒否、設定ファイル経由の拒否
  - `Timer.__init__` が `Terminal` より先に `TimerClock` を作ること
  - `TerminalContext` はカーソルを戻して例外を素通しすること
- 追試: `pytest tests` 138 passed / `ruff format --check`（24 files
  already formatted）/ `ruff check` All checks passed /
  `basedpyright` 0 errors / `mypy` Success。
- 行長: 変更した全ファイルに 78 **文字**超えの行は無い。
  `src/tmr/timer.py:58`（79 文字）は今回の変更より前からある docstring
  （`git blame` で確認）で、`CLAUDE.md:3,175,176` も既存の行。
- 指示範囲外の変更は混ざっていない。
