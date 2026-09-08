# TODO-012 verifier への追加依頼 3（最終検証）

さらに追加実装が入った。**もう一度、全体を**確かめる。修正はしない。

追加で入ったもの:
- `PomodoroConfig` を frozen（読み取り専用）にした
- 例外メッセージを `must be a finite number > 0` に直した
- コメント・docstring の追記
- **アラームの 3 オプション（`--alarm-count` / `--alarm-sec1` /
  `--alarm-sec2`）に検証を追加**
- `README.md` の `timer --help` を更新

## 確かめること

### 1. 前回までの検証を、もう一度全部やり直す

`archives/agents/TODO-012/verifier-task.md` の 1〜4 と
`archives/agents/TODO-012/verifier-task2.md` の 2〜4 を、すべて再実行する。

### 2. アラームの異常値（すべて実際に動かす）

| コマンド | 期待 |
|---|---|
| `uv run tmr timer 1 --alarm-count -1` | usage error（終了コード 2） |
| `uv run tmr timer 1 --alarm-sec1 -1` | usage error（終了コード 2） |
| `uv run tmr timer 1 --alarm-sec2 -1` | usage error（終了コード 2） |
| `uv run tmr timer 1 --alarm-sec1 nan` | usage error（終了コード 2） |
| `uv run tmr timer 1 --alarm-sec2 inf` | usage error（終了コード 2） |

### 3. アラームの正常値（**0 は通らないといけない**）

| コマンド | 期待 |
|---|---|
| `uv run tmr timer 1 --alarm-count 0` | 起動する（usage error にならない） |
| `uv run tmr timer 1 --alarm-sec1 0 --alarm-sec2 0` | 起動する |

`q` で抜けるか `timeout` で止めてよい。usage error になっていなければよい。

### 4. `README.md` との照合

`COLUMNS=80` で `uv run tmr --help` / `timer --help` / `pomodoro --help` を
取り直し、`README.md` の記載と**一字一句**一致するか確かめる。
一致しない箇所は、どの行がどう違うかを報告する（直さない）。

### 5. 検証コマンド

```
uv run pytest tests
uv run ruff format --line-length 78 src tests
uv run ruff check --extend-select I src tests
uv run basedpyright src tests
uv run mypy src tests
```

`mise run` は使わない。`ruff check` に `--fix` は付けない。

## 報告

`archives/agents/TODO-012/verifier-report3.md` に、実行したコマンド、
実際の出力（要点）、合否を書く。**通らなかったものは省かず全部書く。**
返事は 5 行以内。
