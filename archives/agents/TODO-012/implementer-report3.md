# TODO-012 implementer report 3（2 回目の reviewer 指摘の反映 + アラームの検証）

対象: `implementer-task3.md` の E〜H。

## E. `PomodoroConfig` を frozen にする

- `src/tmr/pomodoro.py:12` — `@dataclass` を `@dataclass(frozen=True)` に
  変更。事前に `grep` でフィールドへの代入箇所が無いことを確認済み
  （`src`/`tests` とも属性の読み出ししか無い）。
- `tests/test_pomodoro.py:47-57` — 構築後の代入が
  `dataclasses.FrozenInstanceError` になるテストを追加
  （`# type: ignore[misc]` は型チェッカーが読み取り専用属性への代入を
  静的に検出するため、意図的な代入であることを示す既存の書き方
  `tests/test_terminal.py` に倣った）。

## F. 例外メッセージを直す

- `src/tmr/clock.py:25-27` — `t_limit must be > 0: ...` を
  `t_limit must be a finite number > 0: ...` に変更。
- `src/tmr/pomodoro.py:24-26` — 同様に
  `{name} must be a finite number > 0: {name}={value}` に変更。
- 既存テストはメッセージ文言を見ていなかったため、テスト側の追随は
  不要だった。

## G. 小さな注釈を足す

- `src/tmr/pomodoro.py:21` — `__post_init__` のループの直前に
  「時間のフィールドを足したら、ここにも足す」と 1 行のコメントを追加。
- `src/tmr/cli.py:22-25` — `_reject_non_finite` の docstring に、
  `ctx`/`param` を使わないのは `click` のコールバック規約で 3 引数を
  受けているだけだと分かる一言を追加。

## H. アラームの 3 オプションにも同じ検証を入れる

- `src/tmr/cli.py:59-80` — `timer` の `--alarm-count` を
  `click.IntRange(min=0)` に、`--alarm-sec1`/`--alarm-sec2` を
  `click.FloatRange(min=0)`（`min_open` は付けない）＋既存の
  `callback=_reject_non_finite` に変更。
- `src/tmr/timer.py:4,27-37` — `AlarmParams`（既に frozen）に
  `__post_init__` を追加。`count < 0` と、`sec1`/`sec2` が
  `not math.isfinite(value) or value < 0` のときにそれぞれ
  `ValueError`（F と同じ言い回し）。
- `tests/test_cli.py:88-135` — `--alarm-count -1`、
  `--alarm-sec1`/`--alarm-sec2` の負値、`--alarm-sec1 nan`、
  `--alarm-sec2 inf` が終了コード 2 になることと、
  `--alarm-count 0`・`--alarm-sec1 0` が通ることを確認するテストを追加。
- `tests/test_timer.py:12-33` — `AlarmParams` の
  `count`/`sec1`/`sec2` それぞれの不正値（負値・`nan`・`inf`）が
  `ValueError` になること、`AlarmParams(0, 0.0, 0.0)` が通ることを確認。
- 既存の `AlarmParams(...)` 呼び出し（`tests/test_timer.py`、
  `tests/test_integration_alarm.py`、`src/tmr/timer.py` の
  `DEF_ALARM`）はすべて正の値のため、影響が無いことを確認済み。

## README.md

- `timer --help` の出力が変わった（`--alarm-count`/`--alarm-sec1`/
  `--alarm-sec2` に `RANGE` と `[default: ...; x>=0]` が付く）ため、
  `COLUMNS=80` で実出力を取り直して `README.md` の該当ブロックを
  差し替えた。
- `pomodoro --help` は変化していないことを実出力で確認し、
  変更していない。

## 検証結果

- `uv run pytest tests -q` — 138 passed
- `uv run ruff format --line-length 78 src tests` — 変更 3 ファイルを
  含め整形。以降は unchanged
- `uv run ruff check --fix --extend-select I src tests` — All checks
  passed!
- `uv run basedpyright src tests` — 0 errors, 0 warnings, 0 notes
- `uv run mypy src tests` — Success: no issues found in 24 source files
- `uv run tmr pomodoro -w 0.1 -b 0.1 -l 0.1 -c 2` — 実行し WORK フェーズが
  進むことを確認（`q` で終了、exit 0）。
- `uv run tmr timer 1 --alarm-count 0` — 実行しエラーにならないことを
  確認（`q` で終了、exit 0）。
- `COLUMNS=80 uv run tmr timer --help` / `pomodoro --help` の実出力を
  それぞれ確認し、`timer` 側のみ `README.md` を更新した。
- 行長: 文字数ベースで 78 文字超えの行が無いことを Python の `len()` で
  確認（`src/tmr/timer.py:58` はバイト数計算だと超えて見えるが、
  今回の変更より前からある docstring 行で対象外）。

## 判断が要る点・残る懸念

- 特に判断が要る点は無し。E〜H はすべて完了。
- 範囲外（reviewer 報告 2 の 4 で「今回は範囲外」とされた内容を
  今回 H で取り込んだので、他に残る範囲外の指摘は無い）。
- `t_limit` を後から代入されたときの防御（報告 1 の 3）は、
  指示どおり TODO-013 に残したまま手を入れていない。
