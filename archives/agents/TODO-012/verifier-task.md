# TODO-012 verifier への依頼

## 目的

TODO-012 の実装が指示どおりか、検証が通るかを確かめる。**修正はしない。**

## 確かめること

### 1. 元の現象が直っているか（すべて実際に動かす）

端末が要るコマンドは pty で動かす。例:
`timeout 8 script -qec "uv run tmr timer 0" /dev/null`

| コマンド | 期待 |
|---|---|
| `uv run tmr timer 0` | usage error（終了コード 2）。トレースバックが出ない |
| `uv run tmr timer -- -1` | usage error（終了コード 2）。アラームが鳴り続けない |
| `uv run tmr pomodoro -c 0` | usage error（終了コード 2）。**固まらない** |
| `uv run tmr pomodoro -c -1` | usage error（終了コード 2）。**固まらない** |
| `uv run tmr pomodoro -w 0` | usage error（終了コード 2） |

### 2. 正常系が壊れていないか

- `uv run tmr pomodoro -w 0.1 -b 0.1 -l 0.1 -c 2` が**通ること**
  （0 より大きい小数は弾いてはいけない）。`q` で抜ける、または
  `timeout` で止めてよい。usage error になっていないことが分かればよい
- `uv run tmr timer 1` が起動すること（すぐ止めてよい）

### 3. 検証コマンド

```
uv run pytest tests
uv run ruff format --line-length 78 src tests
uv run ruff check --extend-select I src tests
uv run basedpyright src tests
uv run mypy src tests
```

**`mise run` は使わない**（`uv.lock` を消して sync し直すため）。
`ruff check` は `--fix` を付けずに実行すること（確認だけなので直さない）。

### 4. 文書の照合

実装者は「`timer --help` の出力は `MINUTES` が `click.argument` なので
見た目が変わらず、README の変更は不要」と判断した。**これを実際に確かめる。**

- `uv run tmr timer --help` の実出力と `README.md` の記載が一致するか
- `uv run tmr pomodoro --help` の実出力と `README.md` の記載が一致するか
- `uv run tmr --help` も載っていれば同様に照合する

一致しない箇所は、**どの行がどう違うか**を報告する（直さない）。

## 報告

`archives/agents/TODO-012/verifier-report.md` に、実行したコマンド、
実際の出力（要点）、合否を書く。**通らなかったものは省かず全部書く。**
返事は「終わったか・報告ファイルのパス・判断が要る点」の 5 行以内。
