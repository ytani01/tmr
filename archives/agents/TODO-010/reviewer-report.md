# TODO-010 reviewer 報告

対象: `git diff HEAD` + 未追跡の `src/tmr/clock.py` / `src/tmr/view.py` /
`tests/test_clock.py` / `tests/test_view.py`（ブランチ develop）。

## 結論

**挙動は変わっていない**（下記「実測」参照）。**要修正は 0 件。**
検討 4 件、好みの範囲 3 件。

## 実測でやったこと

1. 旧 `timer.py` を `git show HEAD:src/tmr/timer.py` から取り出し、
   相対 import だけ絶対 import に直したものを scratchpad に置き、
   **旧 `Timer.display()` と新 `TimerView.display()` を総当たりで突き合わせた**。
   - 端末幅 0〜129、`t_limit` = 60.0 / 3661.0、経過率 0 / 50 / 85 / 96 /
     100 / 150%、`is_paused` × `is_active` × `alarm_active` の全組み合わせ
   - 比較したもの: `click.echo` / `click.secho` の呼び出し（`click.style` の
     引数 = 色・bold・blink を含む）、各列の `use` / `value` / `color`、
     `ProgressBar.get_str()` に渡る `bar_len` と `stop`
   - 結果: **12480 ケース、差分 0**
   - 範囲外: タイトルの `width` は 0 のみで試した（`width=16` は
     `col["title"].value` が事前に詰められた文字列になるだけで、
     旧 `PomodoroTimer` が `f"{tt:16s}"` を渡していたのと同一。
     `tests/test_view.py::test_title_width_in_col` と
     `tests/test_pomodoro.py` が押さえている）
2. `uv run pytest tests -q` → 97 passed
3. `uv run ruff format --line-length 78 --check src tests` → 24 files already
   formatted / `uv run ruff check --extend-select I src tests` → All checks passed
4. Python で 1 行の**文字数**を数え直した（`awk length` はバイト数で
   日本語行が誤検出される）。src / tests で 78 文字超は
   `src/tmr/timer.py:45`（79 文字、旧 docstring そのまま）と
   `tests/test_terminal.py`（今回の差分外）のみ

### 依頼文の 1〜4 について読んで確かめたこと

- **`TimerClock`**（1）: `tick()` / `forward()` / `backward()` の式は旧
  `main()` / `fn_forward()` / `fn_backward()` と文字どおり同じ。
  `start()` が `is_paused = False` も行うのは、旧 `main()` が
  `t_start` / `t_elapsed` と一緒に同じことをしていたのと一致する
- **削除順**（2）: 旧 `COL_PRIORITY` は末尾から `pop` なので
  date→time→elapsed→rate→limit→pbar→state→title→remain。
  新 `priority` は date=1 … remain=9 の昇順で同じ。
  `while ... pop()` → `for` への書き換えは、`term.width >= 0` なら
  ループの停止条件が同値（幅が負のときだけ、旧は IndexError、新は
  `!?` 表示。実質は改善）
- **フェーズ制御**（3）: `main()` の戻り値は `quit_by_quitcmd` のみで
  変わっていない。`fn_next` は `enable_next` が偽なら即 return、
  真なら `is_active=False` だけで `quit_by_quitcmd` を触らない（旧と同じ）
- **`phases()`**（4）: 並び・色・秒数・`while True` の繰り返しは旧
  `run()` と同じ。`_run_timer` の呼び出し回数と引数は
  `tests/test_pomodoro.py` が押さえている

### テストの引き継ぎ

旧 `tests/test_timer.py` の 21 ケースを 1 つずつ突き合わせた。
**落ちたケースは無い**（表示系 6 件は `test_view.py` へ、`fn_forward` /
`fn_backward` の上限・下限のケースは `test_clock.py` の
`test_forward` / `test_backward` へ移動）。新規に 15 件ほど増えている。

---

## 検討

### 1. `src/tmr/timer.py:74` — `self.t_limit` がどこからも読まれない

`grep -rn t_limit src tests` の結果、`Timer.t_limit` は代入だけで、
src / tests のどこからも読まれない（時間の計算は `self.clock.t_limit`、
表示は `clock.t_limit`、`ProgressBar` は `TimerView.__init__` の引数）。

困るのは、**旧コードでは `timer.t_limit = X` に意味があった**こと
（旧 `tests/test_timer.py` が実際にそう書いていた）。今は同じことを
しても何も起きない。`Timer` はライブラリとして使う想定（`CLAUDE.md`
の Note）なので、黙って効かない属性が残るのは事故のもと。

消すか、`clock.t_limit` を返す読み取り専用の property にするのが素直。
実装担当も「範囲外と判断して残した」と報告しているので、判断は管理者に。

### 2. `CLAUDE.md:67` — 「表示項目を足すときは、ここに 1 行足すだけ」は言い過ぎ

`TimerView.col_list()` に 1 行足しただけでは、その列の `value` は
空のままで画面に出ない。`display()`（`view.py:118-131`）で
`self.col["..."].value = ...` を書くところまでが必要
（`title` のように `__init__` で入れる場合を除く）。

旧文の「両方に足す」が「1 行足すだけ」になったぶん、**やることが
1 つ抜けて読める**。「`col_list()` に 1 行足し、`display()` で値を入れる」
のように直すのが正確。

### 3. `src/tmr/view.py:71` — `self.title` が `__init__` 以降使われない

`display()` は `self.col["title"]` しか見ない。`view.title` を後から
書き換えても表示は変わらないので、1 と同じ種類の罠になる。
`__init__` のローカル変数で足りる。

### 4. `src/tmr/view.py:74` — `t_limit` が `ProgressBar` にだけ焼き付く

`display()` は毎回 `clock.t_limit` を読むのに、`ProgressBar` は
`__init__` 時点の `t_limit` を持ったまま。両者がずれると
**プログレスバーの目盛りだけが古い値で描かれる**。

今は `Timer.__init__` が同じ値を両方へ渡すので実害は無い。ただし
`tests/test_view.py:143`（`clock.t_limit = 100.0` を後から書く）が、
まさにずれた状態を作っている（`ProgressBar` がモックなので露見しない）。
`TimerView` が `t_limit` を受け取らず、`display()` の中で
`self.pbar` に `clock.t_limit` を渡す形にできれば二重持ちが消える
（`ProgressBar` の API 変更が要るので、やるなら別項目）。

---

## 好みの範囲

### 5. `src/tmr/timer.py:216-220, 238-242, 248-252` — 同じ 5 行が 3 回

`self.view.display(self.clock, is_active=..., alarm_active=...)` が
3 箇所に丸ごと繰り返されている。旧は `self.display()` の 1 行だった。
private な `_display()` を 1 つ置くと、引数を足すときの直し漏れが減る。

### 6. `src/tmr/view.py:157` — `sorted()` を毎フレーム作っている

`priority` は実行中に変わらないので `__init__` で 1 度でよい。
0.2 秒に 1 回・9 要素なので実害は無い。

### 7. `src/tmr/pomodoro.py` — このモジュールだけログが無い

`CLAUDE.md` のログ規約（クラス本体に `__log = getLogger(__qualname__)`）に
対して、`PomodoroTimer` には `__log` が無い。**旧からそうなので今回の
差分の問題ではない**が、`phases()` を新設した今が直しどきではある。

---

## 範囲外の気づき（今回の差分の問題ではない）

- `TimerClock.rate` は `t_limit=0` でゼロ除算になる。`tmr timer 0` で
  再現するはず（**未確認**。コードを読んだだけ）。旧 `display()` も
  同じ式なので挙動は変わっていない。依頼文が「仕様を足さない」と
  指示していたとおりの状態
- `phases()` は `cycles=0` のとき何も yield せずに回り続ける
  （`tmr pomodoro -c 0` で固まる）。旧 `run()` の
  `while True: for i in range(0):` も同じで、挙動は変わっていない
- `TimerView.display()` の点滅条件（`pause_blink` と、満了時の `state`）に
  直接のテストが無い。旧にも無く、今回の総当たり比較では
  `click.style(blink=...)` まで一致を確認済み。`CLAUDE.md` に明記された
  仕様なので、テストを 1 件足しておくと安心
