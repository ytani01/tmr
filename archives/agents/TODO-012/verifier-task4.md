# TODO-012 verifier への依頼 4（最終確認）

アラームの間隔に上限（1 日 = 86400 秒 = `timefmt.SEC_DAY`）が入った。
これが最後の確認。修正はしない。

## 確かめること

### 1. これまでの検証を全部やり直す

`verifier-task.md` の 1〜4、`verifier-task2.md` の 2〜4、
`verifier-task3.md` の 2〜4 を、すべて再実行する。

### 2. 上限の追加分（すべて実際に動かす）

| コマンド | 期待 |
|---|---|
| `uv run tmr timer 1 --alarm-sec1 1e18` | usage error（終了コード 2） |
| `uv run tmr timer 1 --alarm-sec2 1e18` | usage error（終了コード 2） |
| `uv run tmr timer 1 --alarm-sec1 86401` | usage error（終了コード 2） |
| `uv run tmr timer 1 --alarm-sec1 86400` | **通る**（上限ちょうど） |
| `uv run tmr timer 1 --alarm-count 99999` | **通る**（count に上限は無い） |

端末が要るものは pty で動かす。`q` か `timeout` で止めてよい。

### 3. `README.md` との照合

`COLUMNS=80` で `uv run tmr --help` / `timer --help` / `pomodoro --help` を
取り直し、`README.md` の記載と**一字一句**一致するか確かめる。
一致しない箇所は、どの行がどう違うかを報告する（直さない）。

### 4. 検証コマンド

```
uv run pytest tests
uv run ruff format --line-length 78 src tests
uv run ruff check --extend-select I src tests
uv run basedpyright src tests
uv run mypy src tests
```

`mise run` は使わない。`ruff check` に `--fix` は付けない。

## 報告

`archives/agents/TODO-012/verifier-report4.md` に、実行したコマンド、
実際の出力（要点）、合否を書く。**通らなかったものは省かず全部書く。**
返事は 5 行以内。
