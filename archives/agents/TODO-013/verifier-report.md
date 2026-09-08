# TODO-013 検証報告（verifier）

## 1. `uv run pytest tests`

終了コード 0。148 件全通過。

```
============================= test session starts ==============================
...
tests/test_cli.py ......................                                 [ 14%]
tests/test_clock.py .............                                        [ 23%]
tests/test_config.py .............                                       [ 32%]
tests/test_integration_alarm.py ..                                       [ 33%]
tests/test_mylog.py ........                                             [ 39%]
tests/test_pomodoro.py .......................                           [ 54%]
tests/test_progress_bar.py .............                                 [ 63%]
tests/test_terminal.py ...                                               [ 65%]
tests/test_timefmt.py .......                                            [ 70%]
tests/test_timer.py ..............................                       [ 90%]
tests/test_view.py ..............                                        [100%]

============================= 148 passed in 0.63s ==============================
```

## 2. lint（個別コマンド、`mise run` は未使用）

すべて終了コード 0、追加の整形なし。

```
=== ruff format ===
24 files left unchanged
=== ruff check ===
All checks passed!
=== basedpyright ===
0 errors, 0 warnings, 0 notes
=== mypy ===
Success: no issues found in 24 source files
```

## 3. 古い API の残存確認

`ProgressBar.total` / `ProgressBar(total=...)` / `TimerView(term, t_limit, ...)`
（3 引数版）を `src` / `tests` / `README.md` / `docs` で `grep` したが、
いずれも残っていない。`TimerView(` の呼び出しは 3 箇所とも新しい
2 引数版（`term, title`）になっている。

## 4. 実動確認

端末が無い（`tty` は「tty ではありません」、`TERM=screen-256color`）ため、
`script` コマンドで疑似端末を作って実行した。

- `uv run tmr timer 0.1` は `MINUTES` が整数専用のオプションのため
  `Invalid value for 'MINUTES': '0.1' is not a valid integer range.` で
  弾かれた（依頼文の例がそのままでは通らない）。代わりに `uv run tmr timer 1`
  を 5 秒だけ動かし、プログレスバーが `0.0%` → `6.7%`（`>` の数が増える）
  → 残り時間が `0m60s` → `0m55s` と減っていくのを確認した。異常なし。
- `uv run tmr pomodoro -w 0.1 -b 0.1 -c 2` を実行し、WORK フェーズの
  進捗率が `0.0%` から `96.9%` まで単調に増えるのを確認した
  （0.1 分 = 6 秒の間、`3.4%` 刻みで増加）。100% に到達した後は
  アラームが鳴り続けて `100.0%` のまま止まって見えるが、これは
  疑似端末からキー入力を送っていないための想定内の停止であり、
  今回の変更由来の不具合ではないと判断した。

## 5. 追加テスト 2 件が意味を持つか

`git stash` で `src/tmr/progress_bar.py` / `timer.py` / `view.py` の
3 ファイルだけを変更前（`HEAD` = TODO-012 の状態）に戻し、新規追加した
2 件のテストだけを流したところ、両方とも変更前のコードに対して
失敗することを確認した。

```
tests/test_progress_bar.py::test_get_str_total_not_kept FAILED
tests/test_view.py::test_pbar_uses_current_t_limit ERROR
```

- `test_get_str_total_not_kept`:
  `TypeError: ProgressBar.get_str() takes 2 positional arguments but 3
  positional arguments (and 2 keyword-only arguments) were given`
- `test_pbar_uses_current_t_limit`:
  `TypeError: TimerView.__init__() missing 1 required positional
  argument: 'title'`

いずれも API のシグネチャが変わったことによる `TypeError` であり、
「値の食い違い」そのものを検出しているわけではない。ただし
TODO-013 本文にあるとおり、現状の本番コードでは `Timer.__init__` が
`clock` と `view` に同じ `t_limit` を渡すだけで、実行中に
`clock.t_limit` を書き換える経路が無い（`grep` で確認済み、
`t_limit` を後から代入している箇所はコンストラクタ以外に無い）。
そのため「値がずれる」状況を作るには、そもそも API を変えて
`display()` の都度 `t_limit` を渡す形にするしかなく、
このテストが（シグネチャ変更を含めて）変更前のコードで落ちることは、
このテストが変更の意図（`t_limit` の受け渡し方を変えた）を
捉えている根拠として妥当だと判断した。ただし「値そのものの食い違いを
再現して検出できているか」までは、本番コードに再現条件が無いため
確かめられていない。この点は判断が要ると思う。

`git stash pop` で作業ツリーは元の状態（未コミットの変更あり）に
復元済み。

## 6. 変更ファイルの一覧と対象範囲

```
$ git status --short
 M TODO.md
 M src/tmr/progress_bar.py
 M src/tmr/timer.py
 M src/tmr/view.py
 M tests/test_progress_bar.py
 M tests/test_timer.py
 M tests/test_view.py
```

- `TODO.md` は担当の見込み行（`implementer + reviewer + verifier` →
  `reviewer + verifier`）の 1 行のみで、依頼の「対象外」の記述と一致。
- 残り 6 ファイルは依頼どおり `src/tmr/progress_bar.py` /
  `src/tmr/timer.py` / `src/tmr/view.py` とそれぞれのテストで、
  依頼の対象範囲と一致。指示に無いファイルの変更は見当たらない。
- 差分の内容も依頼どおり: `ProgressBar.__init__` から `total` を削除
  （`bar_length` が第 1 引数）、`get_str(val, total, *, bar_len, stop)` /
  `display(val, total, ...)` へ変更、`TimerView.__init__(term, title)`
  へ変更、`display()` で毎回 `clock.t_limit` を渡すよう変更、
  `Timer.__init__` の呼び出しを追随。

## 7. 確かめられなかったこと・判断が要る点

- 追加テスト 2 件は API シグネチャの変更によって変更前コードで
  `TypeError` になることは確認したが、「値の食い違いそのもの」を
  検出する形になっているかは、本番コードに `t_limit` を書き換える
  経路が無いため確かめられなかった（上記 5 節参照）。設計として
  妥当かどうかは判断が要ると思う。
- 依頼文にあった `uv run tmr timer 0.1` はそのままでは
  `click.IntRange` に弾かれて実行できない（`MINUTES` は整数のみ）。
  依頼文の誤りの可能性があるため報告する。
- 端末が無い環境での実動確認のため、実際のインタラクティブな
  ターミナルでの見え方（色付けや点滅、キー入力での次フェーズ移行）は
  未確認。
