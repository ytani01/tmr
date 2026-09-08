# TODO-012 verifier への追加依頼（2 回目の検証）

reviewer の指摘を受けた追加実装が入った。**もう一度、全体を**確かめてほしい。
修正はしない。

追加で入ったもの:
- `PomodoroConfig.__post_init__` での 4 項目の検証
- `nan` / `inf` の排除（`TimerClock` / `PomodoroConfig` / CLI のコールバック）
- CLI テストの強化と負値のケース追加
- `CLAUDE.md` への 4 行の追記

## 確かめること

### 1. 前回の検証を、もう一度全部やり直す

`archives/agents/TODO-012/verifier-task2.md` ではなく、
`archives/agents/TODO-012/verifier-task.md` の 1〜4 をそのまま再実行する。

### 2. 追加分（すべて実際に動かす）

| コマンド | 期待 |
|---|---|
| `uv run tmr pomodoro -w nan` | usage error（終了コード 2）。固まらない |
| `uv run tmr pomodoro -w inf` | 同上 |
| `uv run tmr pomodoro -b nan` | 同上 |
| `uv run tmr pomodoro -l inf` | 同上 |
| `uv run tmr pomodoro -w -1` | usage error（終了コード 2） |
| `uv run tmr pomodoro -c -1` | usage error（終了コード 2）。固まらない |
| `uv run tmr timer -- -1` | usage error（終了コード 2） |

端末が要るものは pty で動かす
（例: `timeout 8 script -qec "uv run tmr pomodoro -w nan" /dev/null`）。

### 3. 設定ファイル経由も試す

`XDG_CONFIG_HOME` を一時ディレクトリに向け、
`$XDG_CONFIG_HOME/tmr/config.toml` に次を書いて、それぞれ
usage error（終了コード 2）になり**固まらない**ことを確かめる。

- `[pomodoro]` の `work-time = nan`
- `[pomodoro]` の `work-time = inf`
- `[pomodoro]` の `cycles = 0`
- `[timer]` の `minutes = 0`

### 4. 正常系

- `uv run tmr pomodoro -w 0.1 -b 0.1 -l 0.1 -c 2` が通ること
- `uv run tmr timer 1` が起動すること
- 設定ファイルに正常な値（`[pomodoro]` の `work-time = 0.1`）を書いた場合も通ること

## 報告

`archives/agents/TODO-012/verifier-report2.md` に、実行したコマンド、
実際の出力（要点）、合否を書く。**通らなかったものは省かず全部書く。**
返事は 5 行以内。
