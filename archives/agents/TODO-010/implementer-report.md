# TODO-010 implementer 報告

`Timer` を分割し、引数をデータクラスにした。依頼文
（`archives/agents/TODO-010/instructions.md`）の 1〜6, 8 を実施。
**7（`CLAUDE.md` の更新）はやっていない**（下記「判断が要る点」）。

## 変更したファイル

### 新規

- `src/tmr/clock.py`（全体, 1-87）— `TimerClock`。
  `start()` 22-40 / `tick()` 42-51 / `toggle_pause()` 53-56 /
  `forward()` 58-64 / `backward()` 66-72 /
  `remain` 74-77 / `rate` 79-82 / `is_timeup` 84-87。
  式は旧 `Timer.main()` / `fn_forward()` / `fn_backward()` からそのまま移した。
- `src/tmr/view.py`（全体, 1-205）— `TimerTitle` 18-32 /
  `TimerCol` 35-49 / `TimerView` 52-205。
  `col_list()` 84-104 が表示順、`priority` が削除の優先順位。
  `PERCENT_COLOR` / `PBAR_LEN_MIN` / `STAT_STR_PAUSE` / `STAT_STR_TIMEUP` も移した。
- `tests/test_clock.py`（新規, 149 行）
- `tests/test_view.py`（新規, 213 行）

### 変更

- `src/tmr/timer.py`
  - `AlarmParams`（18-24）を追加、`type AlarmParams = tuple[...]` は削除。
  - `TimerCol` / `col_list()` / `display()` / `PERCENT_COLOR` /
    `COL_PRIORITY` / `PBAR_LEN_MIN` / `STAT_STR_*` を削除（`view.py` へ）。
  - `DEF_TITLE`（58）は `TimerTitle`、`DEF_ALARM`（59）を追加。
  - `__init__`（61-92）で `TimerClock` と `TimerView` を作る。
    `Terminal` は `Timer` が作って `TimerView` に渡す。
  - `main()`（190-255）— `self.clock.start()` / `self.clock.tick()` /
    `self.clock.is_timeup`、表示は `self.view.display(...)` を直接呼ぶ
    （3 か所: 216, 238, 248）。
  - `fn_pause` / `fn_forward` / `fn_backward`（283-295）は `clock` に委譲。
    `fn_quit` / `fn_next` は `self.clock.is_paused = False`。
  - `ring_alarm()`（317-337）— `AlarmParams` を展開して `args=` に渡す。
- `src/tmr/pomodoro.py` — `phases()`（22-51）を追加。
  `run()`（65-73）は `for title, sec in phases(...)`。
  `_run_timer(title: TimerTitle, seconds: float)`（75-82）。
  桁揃え（16 桁）は `TimerTitle.width` へ移した（`TITLE_WIDTH` 19）。
- `src/tmr/cli.py:13-14`（import）、`154-158`
  （`Timer(TimerTitle(...), limit, AlarmParams(...))`）。CLI オプションは不変。
- `tests/test_timer.py` — 新構成に合わせて全面的に書き直し。
  表示関係のケース（レイアウト、色、`[PAUSE]`、時間表示、`!?`）は
  `tests/test_view.py` へ移した。`timer.t_elapsed` などは
  `timer.clock.elapsed`。`main()` の時刻は `tmr.clock.time` をモック。
  `test_init_defaults` / `test_main_loop_display` /
  `test_ring_alarm_inactive` / `test_get_key_name_unknown` を追加。
- `tests/test_pomodoro.py` — `phases()` のテスト 2 件を追加
  （1 サイクル分の並び・色・秒数、サイクルの繰り返し）。
  `_run_timer` の引数は `TimerTitle` になったので
  `call_args[0][0].display_text` で見る。
- `tests/test_cli.py:2,25` / `tests/test_config.py:9,52,64,75,96` —
  `("Timer", "blue")` などの期待値を `TimerTitle(...)` に。
- `tests/test_integration_alarm.py:5,20,45` — `alarm_params` を `AlarmParams` に。

## 設計から外した点・判断したこと

1. **`TimerClock.start()` で `is_paused = False` も行う。** 旧 `main()` が
   `self.t_start` / `self.t_elapsed` と一緒に `is_paused = False` を
   設定していた。`Timer` 側に `is_paused` を残さない方針なので、
   start() に含めた（挙動は同じ）。`fn_quit` / `fn_next` の解除は
   `self.clock.is_paused = False` で直接行っている。
2. **`TimerTitle.display_text`（property）を足した。** `width > 0` のとき
   `f"{text:{width}s}"` を返す。依頼文には整形の置き場所の指定が無かった。
3. **省略のループを `while ... pop()` から `for`（priority 昇順）に変えた。**
   結果の削除順は同じ。旧実装は幅が負のとき空リストへの `pop()` で
   IndexError になったが、新実装は `col_disp` が空になれば止まる
   （`view.py:158-163`）。`term.width >= 0` なら差は無い。
4. **`Timer.display()` は残していない。** 依頼文の「`Timer` に残るのは …」に
   無かったため、`self.view.display(...)` を直接呼ぶ形にした。

## 検証

すべてリポジトリルートで実行。

| コマンド | 結果 |
|---|---|
| `uv run pytest tests -q` | 97 passed（終了コード 0） |
| `uv run ruff format --line-length 78 src tests` | 2 files reformatted, 22 unchanged（0） |
| `uv run ruff check --fix --extend-select I src tests` | All checks passed!（0） |
| `uv run basedpyright src tests` | 0 errors, 0 warnings, 0 notes（0） |
| `uv run mypy src tests` | Success: no issues found in 24 source files（0） |

`mise run` は使っていない。整形後にもう一度 pytest を流して 97 passed を確認した。

### 手元での動作確認

`timer` は `MINUTES` が `int` なので `0.05` は渡せない
（`Error: Invalid value for 'MINUTES'`）。この端末は対話できないので、
`script -qec "stty rows 24 cols 100; ..."` で疑似端末を作り、出力を見た。
キー入力ができないため、アラームは `timeout` で打ち切った。

- `uv run tmr pomodoro -w 0.02 -b 0.02 -l 0.02 -c 2` —
  `WORK:1/2        `（cyan、16 桁）が出て、date, time, title, limit,
  rate, elapsed, pbar, remain の順に並ぶ（`state` は空なので出ない）。
  経過率に応じて white → yellow → red に変わり、プログレスバーが伸び、
  満了で `\a` が鳴った。
- `uv run tmr timer 1 -t Test -c green` — `Test`（green、桁揃え無し）で
  正常に動く。

## 残る懸念・範囲外の気づき

- **`CLAUDE.md` を更新していない。** 依頼文の 7 に入っていたが、
  実装担当は `CLAUDE.md` を触らない決まりなので手を付けなかった。
  直す必要があるのは次の 3 か所（管理者または wording へ）:
  1. 「`Timer` が本体」— 時刻は `clock.py` の `TimerClock`、表示は
     `view.py` の `TimerView`、`Timer` はメインループとキー操作・
     アラームだけ、という記述に。`t_start` をずらす話は `TimerClock` の説明へ。
  2. 「表示は 2 つのリストで決まる」— `col_list()` の並びが表示順、
     `TimerCol.priority` が小さいものから削られる（1 か所にまとまった）。
     `PERCENT_COLOR` / `PBAR_LEN_MIN` などは `TimerView` にある。
  3. 「テスト」— モック先は `tmr.timer` の `Terminal` / `TimerView`、
     表示は `tmr.view` の `ProgressBar` / `click`、時刻は `tmr.clock` の
     `time`。`term.width` に数値を入れる話はそのまま有効。
- `TimerClock.rate` は `t_limit=0` でゼロ除算になる（現行のまま。
  依頼文の指示どおり仕様を足していない）。
- `tests/test_view.py::test_delete_order` は、`state` の値が空だと
  幅に影響せず削除順が観測できないため、`clock.is_paused = True` にして
  `[PAUSE]` を入れてから測っている。
- `Timer.t_limit` と `TimerClock.t_limit` の 2 か所に同じ値が残っている
  （`Timer.t_limit` は現状どこからも読まれていない）。消すのは範囲外と
  判断して残した。
