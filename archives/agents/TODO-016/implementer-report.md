# TODO-016 implementer 報告

アラームで外部コマンドを呼べるようにする（`--alarm-cmd` / `--cmd`）。

## 変更したファイル

### `src/tmr/timer.py`

- `timer.py:5` — `import subprocess` を追加
- `timer.py:23-49` — `AlarmParams` に `cmd: str | None = None` を追加。
  docstring に「ビープの代わりにシェル経由で 1 回だけ実行する」と明記。
  `__post_init__` の先頭で、`cmd` が `None` でなく `strip()` して空なら
  `ValueError`（`""` / `" "` / `"\t"` を弾く）
- `timer.py:353-370` — `exec_alarm_cmd(cmd)` を新設。
  `subprocess.run(cmd, shell=True, check=False)` を 1 回だけ実行し、
  `returncode` が 0 なら `debug`、非ゼロなら `warning` でログに出す。
  `OSError` を捕まえて `error` でログに出し、そのまま戻る
- `timer.py:372-388` — `thr_alarm()` の引数を
  `(count, sec1, sec2)` から `(params: AlarmParams)` 1 つに変更。
  `params.cmd` があれば `exec_alarm_cmd()` を呼んで **`alarm_active` を
  False にせずに戻る**（キー入力を待つ）。無ければ従来どおりのビープで、
  最後に `alarm_active = False`
- `timer.py:402` — `ring_alarm()` のスレッド引数を
  `args=(self.alarm_params,)` に変更

`cmd` 指定時に `alarm_active` を落とさないので、`main()` のアラーム
ループはキー入力まで回り続ける。`thr_alarm` 自体はすぐ終わるため、
`main()` 末尾の `thr.join()` は待たずに返る。

### `src/tmr/cli.py`

- `cli.py:4` — `import dataclasses`
- `cli.py:87-93` — `timer` に `--alarm-cmd` / `--cmd`
  （`type=str, default=None`, help=`alarm command (instead of beep)`）
- `cli.py:104,114,123` — 引数 `alarm_cmd` を受け、debug ログに出し、
  `AlarmParams(alarm_count, alarm_sec1, alarm_sec2, alarm_cmd)` に渡す
- `cli.py:166-172` — `pomodoro` にも同じオプションを追加
- `cli.py:175-176,186,195` — `PomodoroConfig(...,
  alarm_params=dataclasses.replace(Timer.DEF_ALARM, cmd=alarm_cmd))`。
  未指定なら `Timer.DEF_ALARM` と等しくなる

### `src/tmr/pomodoro.py`

- `pomodoro.py:9` — `from .timer import AlarmParams, Timer`
- `pomodoro.py:21` — `PomodoroConfig` に
  `alarm_params: AlarmParams = Timer.DEF_ALARM`
  （frozen dataclass なので既定値に置ける）
- `pomodoro.py:107-112` — `_run_timer()` が
  `alarm_params=self.config.alarm_params` を `Timer` に渡す

### テスト

- `tests/test_timer.py:56-72` — `cmd` が空文字・空白のみで `ValueError`、
  `None` は可、文字列は可
- `tests/test_timer.py:97-102` — `mock_subprocess` fixture
  （`tmr.timer` の `subprocess` を patch。`run().returncode = 0`）
- `tests/test_timer.py:326-331` — 既存の `test_ring_alarm_and_thread` を
  新しい `thr_alarm(AlarmParams)` の形に合わせて更新
- `tests/test_timer.py:349-405` — 追加した 4 件
  - `test_thr_alarm_cmd`: `subprocess.run` が
    `(cmd, shell=True, check=False)` で **1 回だけ**呼ばれ、
    `click.echo`（ビープ）は呼ばれず、`alarm_active` は True のまま
  - `test_thr_alarm_cmd_nonzero`: `returncode=1` でもビープに戻らない
  - `test_thr_alarm_cmd_oserror`: `OSError` でも例外を投げない
  - `test_main_with_alarm_cmd_failure`: コマンドが失敗しても
    `main()` はキー入力で正常に抜け、`False` を返す
    （実スレッドを動かす経路）
- `tests/test_cli.py:16` — `--alarm-cmd` が help に出ること
- `tests/test_cli.py:182-260` — `--alarm-cmd` / `--cmd` が
  `AlarmParams.cmd` に届くこと、未指定なら `None`、空文字はエラー、
  `pomodoro` では `PomodoroConfig.alarm_params.cmd` に届くこと、
  未指定なら `Timer.DEF_ALARM` と等しいこと
- `tests/test_pomodoro.py:8,248,264-291` — `--alarm-cmd` が help に出る、
  `alarm_params` の既定が `Timer.DEF_ALARM`、`_run_timer()` が
  `alarm_params` を `Timer` に渡すこと

### 文書

- `docs/User.md:48,82` — `timer` / `pomodoro` の help 出力を実出力に更新
- `docs/User.md:202-211` — アラーム節の冒頭に `--alarm-cmd` への言及、
  「鳴らし方の 3 オプションは `timer` だけ」という書き方に修正
  （`--alarm-cmd` は両方で使えるため）
- `docs/User.md:232-260` — 「ベルの代わりにコマンドを実行する」を追加。
  置き換えであること、1 回だけであること、キー入力を待つこと、
  失敗しても続くこと、ポモドーロは全フェーズ共通であること、
  **文字列がそのままシェルに渡る（設定ファイルも同じ）**注意
- `docs/User.md:280` — 設定ファイルの例に `alarm-cmd` を追加
  （`config.py` は click のパラメータ名から自動で受けるので実装変更は不要。
  実際に `[pomodoro] alarm-cmd` が通ることは既存の仕組みどおり）
- `docs/Developer.md:248-256` — アラームの節に `cmd` の説明を追加
- `docs/Developer.md:285` — テストの patch 先の表に `subprocess` を追加
- `README.md` — **変更なし**（help 出力を載せていないため。
  オプション一覧は `docs/User.md` 側にある）

## 検証

すべて `/home/ytani/work/tmr` で実行。

| コマンド | 結果 |
|---|---|
| `uv run pytest tests` | 167 passed（終了コード 0） |
| `uv run ruff format --line-length 78 src tests` | 24 files left unchanged（0） |
| `uv run ruff check --fix --extend-select I src tests` | All checks passed!（0） |
| `uv run basedpyright src tests` | 0 errors, 0 warnings, 0 notes（0） |
| `uv run mypy src tests` | Success: no issues found in 24 source files（0） |

help 出力は `COLUMNS=80 uv run tmr timer --help` /
`uv run tmr pomodoro --help` を実行し、`docs/User.md` に貼った内容と
一致することを確認した。

手元での実行も確認:

```
printf 'q' | uv run tmr pomodoro -w 0.02 -b 0.02 -c 1 \
  --cmd "echo ALARM_RAN >> .../out.txt" -d
```

満了時に `exec_alarm_cmd()` が 1 度だけ走り
（`returncode=0` のログ）、`out.txt` に 1 行だけ書かれ、
`q` を押すまでアラーム状態が続いてから終了した。

## 判断が要る点・気づいたこと

1. **`--cmd ""` を指定すると traceback が出る。**
   `AlarmParams.__post_init__` の `ValueError` がそのまま上がるため。
   `cli.py` の `_reject_non_finite` と同じ形のコールバックを足せば
   usage error（終了コード 2）にできるが、依頼の範囲は
   「`AlarmParams` で `ValueError`」だったので**足していない**。
   `CLAUDE.md` の「CLI とデータクラスの二重で弾く」方針に照らすと
   足す方が揃うので、判断をお願いしたい。
   足す場合は `tests/test_cli.py` の
   `test_timer_alarm_cmd_empty_rejected` も直す必要がある。

2. **`CLAUDE.md` は編集していない。**
   依頼には「設計節に 1〜2 行足す」とあったが、実装担当は `CLAUDE.md` を
   触らない決まりなので、管理者にお願いしたい。案:

   ```
   - `AlarmParams.cmd`（CLI では `--alarm-cmd` / `--cmd`）を指定すると、
     ベルの代わりに `subprocess.run(cmd, shell=True)` を満了時に 1 回だけ
     実行する（TODO-016）。**このとき `alarm_active` は False にしない**
     （キー入力を待つ点をベルと揃えるため）。失敗はログに残すだけで、
     ベルにフォールバックしない。空文字・空白のみの `cmd` は `ValueError`
   ```

   テストの表の `tests/test_timer.py` の行にも
   `/ subprocess`（アラームのコマンド）を足すとよい
   （`docs/Developer.md` には反映済み）。

3. **`thr_alarm()` の引数を `AlarmParams` 1 つにまとめた**
   （依頼の「必要なら整える」に沿った変更）。外部から
   `thr_alarm(count, sec1, sec2)` を呼んでいる箇所はテストだけで、
   そこは更新済み。

4. **範囲外の気づき**: `--alarm-count` / `--alarm-sec1` / `--alarm-sec2` は
   `timer` にしか無く、`pomodoro` は `Timer.DEF_ALARM`（999 回）固定。
   今回の `--alarm-cmd` だけ両方に付いたので、非対称ではある。
   決めごとどおりなので手を入れていない。

---

# 追記: レビュー指摘への対応（2 巡目）

`archives/agents/TODO-016/reviewer-report.md` の指摘 1, 2, 3, 5, 6 と、
管理者の指示に沿って修正した。指摘 4（`CLAUDE.md`）と 7 は触っていない。

## 1. キー入力で外部コマンドも止める（指摘 1）

`subprocess.run` をやめ、`subprocess.Popen` + `communicate()` にした。

- `timer.py:85` — `ALARM_STOP_SEC = 1.0`（止めるときに待つ秒数）
- `timer.py:111-115` — `alarm_proc` / `alarm_proc_ready`（`threading.Event`）
  / `alarm_cmd_stopped` を追加
- `timer.py:360-405` — `exec_alarm_cmd()` が `Popen(...)` で起動し、
  `alarm_proc` に入れて `alarm_proc_ready` を立ててから
  `communicate()` で終了を待つ
- `timer.py:407-431` — `kill_alarm_cmd(proc, sig, name)` を新設。
  `os.killpg(proc.pid, sig)` を送る。`ProcessLookupError`（既に居ない）は
  失敗にしない。それ以外の `OSError` は `error` ログを出して False
- `timer.py:433-478` — `stop_alarm_cmd(thr)` を新設。
  `SIGTERM` → `ALARM_STOP_SEC` 待つ → 止まらなければ `SIGKILL` →
  それでも止まらなければ警告を出して False を返す
- `timer.py:288` — `main()` の末尾を
  `if thr and self.stop_alarm_cmd(thr): thr.join()` に変更。
  **`main()` が返る前に子プロセスは終わっている**（止まらなかったときだけ
  警告を出し、`join()` せずに進む＝固まらせない）

判断したこと:

- **プロセスグループごと落とす**（`start_new_session=True` +
  `os.killpg`）。実測で、`--cmd "sleep 5"` は `sh` が `sleep` を子として
  持つため、`proc.terminate()` では `sh` しか死なず、
  **`sleep` が残って `stdout` のパイプを握り続け**、
  `communicate()` が返らなかった（`cmd not stopped` の警告が出て、
  tmr の終了後も `sleep` が残った）。プロセスグループごとにしたら
  0.05 秒で終わり、残骸も無くなった
- **`alarm_proc_ready`（Event）が要る。** キーを押すのが速いと、
  スレッドが `Popen` を作る前に `stop_alarm_cmd()` が走り、
  「止める相手が居ない」と判断して `join()` で固まる。
  起動を試みたら（失敗しても）立てるイベントで待ってから止める
- 自然に終わったときは今までどおり `alarm_active` を False にせず、
  キー入力を待つ（仕様どおり。変えていない）

## 2. 子プロセスの入出力を端末から切り離す（指摘 5）

- `timer.py:372-388` — `stdin=subprocess.DEVNULL`、
  `stdout` / `stderr` は `subprocess.PIPE` で取り込み、
  `text=True, errors="replace"` で受けて `debug` ログに回す。
  画面には出さない
- 終了コードのログ水準: 0、または自分で止めたとき（`alarm_cmd_stopped`）は
  `debug`、それ以外は `warning`。自分で止めた負の `returncode` を
  失敗として警告しないため

## 3. `--cmd ""` を usage error にする（指摘 2, 3）

- `cli.py:33-43` — `_reject_empty()` を追加
  （`None` は素通し、`strip()` が空なら `click.BadParameter`）。
  `_reject_non_finite` と同じ形
- `cli.py:94, 180` — `timer` / `pomodoro` の両方に `callback=_reject_empty`
- `AlarmParams.__post_init__` の `ValueError` はライブラリ経路用に残した

実測: `tmr timer 1 --cmd ""` / `tmr pomodoro --cmd "  "` とも
`Error: Invalid value for '--alarm-cmd' / '--cmd': must not be empty: ''`
で**終了コード 2**。設定ファイルに `alarm-cmd = ""` を書いた場合も同じ
（テストで固定した）。

## 4. テスト（指摘 6）

`tests/test_timer.py`:

- `mock_subprocess` fixture を `Popen` 用に作り替え、
  `mock_killpg` fixture（`tmr.timer.os.killpg`）を追加
- `_running_proc()` ヘルパー — `communicate()` が
  `threading.Event` を待つ「終わらないコマンド」を作る
- `test_thr_alarm_cmd` — `Popen` の引数
  （`stdin=DEVNULL` / `stdout=PIPE` / `stderr=PIPE` /
  `start_new_session=True`）を固定
- `test_main_quit_with_alarm_cmd` — **cmd 経路で `[Q]` なら
  `main()` が True を返す**（ポモドーロの制御経路。指摘 6 の要のテスト）
- `test_stop_alarm_cmd_sigterm` / `_sigkill` / `_not_stopped` /
  `_already_gone` / `_oserror` / `_beep`
- `test_main_stops_alarm_cmd_by_key` — キー入力で `main()` が
  コマンドを止めてから返る

`tests/test_cli.py`:

- `test_timer_alarm_cmd_empty_rejected` を `exit_code == 2` を見る形に変更
  （`""` / `" "` / `"\t"`）
- `test_pomodoro_alarm_cmd_empty_rejected` を追加

`tests/test_config.py`:

- `test_config_alarm_cmd` — `[timer] alarm-cmd` が `AlarmParams` に届く
- `test_config_alarm_cmd_empty_rejected` — 設定ファイル経由の空文字も
  終了コード 2
- `test_config_pomodoro_alarm_cmd` — `[pomodoro] alarm-cmd` が
  `PomodoroConfig.alarm_params` に届く

## 5. 文書（指摘 1, 5）

- `docs/User.md:244-264` — キーを押すとコマンドも止まること、
  出力は画面に出さずログへ回すこと、`-d` の説明の訂正
  （**失敗は `-d` 無しでも警告として出る**）、コマンドはキーボードを
  読めないこと、空文字は終了コード 2、`subprocess.Popen` への表記変更
- `docs/Developer.md:248-280` — 「アラームのコマンド（`AlarmParams.cmd`）」の
  小節に書き直し。「メインループは止まりません」は
  「**アラームの待ちループ**は止まらないが、**キーを押したあとの
  後始末では待つ**」と書き分けた。プロセスグループごと落とす理由、
  `alarm_proc_ready` が要る理由、`stdin`/`stdout` を切り離す理由を明記
- `docs/Developer.md:200-205` — 値の検証の節に、`--alarm-cmd` も
  二重で弾く（CLI は `_reject_empty`、`AlarmParams` は `ValueError`）と追記
- `README.md` は変更なし（help 出力を載せていないため）

## 検証（2 巡目）

| コマンド | 結果 |
|---|---|
| `uv run pytest tests` | 182 passed（終了コード 0） |
| `uv run ruff format --line-length 78 src tests` | 24 files left unchanged（0） |
| `uv run ruff check --fix --extend-select I src tests` | All checks passed!（0） |
| `uv run basedpyright src tests` | 0 errors, 0 warnings, 0 notes（0） |
| `uv run mypy src tests` | Success: no issues found in 24 source files（0） |

実際に動かした確認（`pty` で端末を作り、`TIME UP` の 0.5 秒後に
`q` を送って計測。`tmr pomodoro -w 0.02 -c 1 --cmd ...`）:

| cmd | `q` を押してから終了まで | 残骸 |
|---|---|---|
| `sleep 5` | **0.05 秒** | 無し（`pgrep sleep` で確認） |
| `echo hello` | 0.05 秒（自然終了後もキーを待った） | 無し |
| `no_such_cmd_xyz` | 0.05 秒。`returncode=127` の警告のみ（`/bin/sh` の "not found" は画面に出ず、ログへ） | 無し |

修正前の同じ手順では、`sleep 5` は 2.05 秒かかったうえ
`cmd not stopped` の警告が出て `sleep` が残った。

`--cmd ""` は終了コード 2、`--help` の出力は `docs/User.md` の
貼り付けと引き続き一致（プログラムで照合）。

## 残る懸念

- **アラームのコマンドが動いている間に `Ctrl-C` を押すと、
  子プロセスが残る。** `start_new_session=True` にしたので、端末からの
  `SIGINT` は子のプロセスグループに届かない。`main()` は
  `KeyboardInterrupt` を捕まえていない（`TerminalContext` が握り潰す）ので
  `stop_alarm_cmd()` も走らない。修正するなら
  `main()` か `TerminalContext` 側で後始末を呼ぶ形になるが、
  範囲を広げないため手を入れていない。判断をお願いしたい
- `ALARM_STOP_SEC = 1.0` は `Timer` のクラス変数で、CLI からは変えられない
  （テストではインスタンス属性で上書きしている）

---

# 追記: 2 巡目レビューへの対応（3 巡目）

`reviewer-report.md` の「2 巡目」の指摘のうち、管理者の線引きに従って
2-1 / 2-4 / 2-5 / 2-6 / 2-8 を直し、2-2 / 2-3 は文書に注意を書いた。
2-7（Windows）と「好みの範囲」の 2 つ目以外は触っていない。

## 直したもの

### 2-1. `Ctrl-C` で子プロセスが残る

- `timer.py:229-247` — `main()` を「`_main()` を呼んで
  `KeyboardInterrupt` を捕まえる」薄い層にした。捕まえたら
  `stop_alarm_cmd(self.alarm_thr)` を通してから `raise` で送出し直す
  （握り潰す `TerminalContext` へ渡る前に止める）。
  docstring に、なぜ届かないのか（子は別セッション）を書いた
- `timer.py:249` — メインループ本体を `_main()` に移した
- `timer.py:112` — `alarm_thr`（アラームのスレッド）を持たせ、
  `_main()` の `ring_alarm()` の直後に入れる（`timer.py:285`）
- `start_new_session=True` は指示どおり残した

### 2-5. 同じ `Timer` で `main()` を 2 回呼べるようにする

- `timer.py:253-257` — `_main()` の冒頭で `alarm_proc` /
  `alarm_proc_ready`（`clear()`）/ `alarm_cmd_stopped` / `alarm_thr` を
  初期化する

### 2-4. pid 再利用の窓

- `timer.py:455-458` — `kill_alarm_cmd()` の中でも、送る直前に
  `proc.poll() is not None` なら送らずに True を返す
- `timer.py:445-450` — **なぜ `Popen.send_signal()` ではなく生の
  `killpg` なのか**をコメント（docstring）に残した。
  「`send_signal()` はシェル 1 つにしか届かない。代わりに、それがやって
  いる『終わった相手には送らない』確認をここで自分で行う」

### 2-6. テストが無関係なプロセスを撃ちうる

- `tests/conftest.py`（新規）— autouse fixture で
  `tmr.timer.os.killpg` を常に塞ぐ。理由も docstring に書いた
- `tests/test_timer.py:110` — モックの `pid` を `12345` から `-1` に
  （`killpg` に渡っても `EINVAL` で当たらない値）
- `killpg` に到達しうる `main()` のテストには `mock_killpg` を付けた

### 2-8. テストの追加

- `test_main_quit_with_alarm_cmd` / `test_main_with_alarm_cmd_failure` に
  `mock_killpg.assert_not_called()`（**自然に終わった／起動に失敗した
  コマンドにシグナルを送らない**）
- `test_thr_alarm_cmd_output_to_log` — 出力をログに回す分岐。
  `LOG_MAX_LEN` で切り詰めることも固定
- `test_thr_alarm_cmd_empty_output_not_logged` — 空の出力は出さない
- `test_stop_alarm_cmd_waits_for_popen` — **`alarm_proc_ready` の競合**。
  `Popen` を 0.2 秒遅らせ、その前に `stop_alarm_cmd()` を呼んでも
  `SIGTERM` が届くこと（必須ではないと言われたが書けたので入れた）
- `test_main_resets_alarm_cmd_state` — 2 回目の `main()` でも止まること
- `test_main_keyboard_interrupt_stops_alarm_cmd` /
  `test_main_keyboard_interrupt_without_alarm` — `Ctrl-C` の後始末

### 任意だった切り詰め（2-2 の後半）

- `timer.py:85` — `LOG_MAX_LEN = 200`
- `timer.py:421-426` — 出力をログに出すときに先頭 200 文字だけにする
  （`-d` で 50MB が画面に流れるのを防ぐ）

## 文書だけにしたもの

- `docs/User.md:264-273` — 「次の書き方は避けてください」として、
  **出力が大量に出るコマンド（`yes`、`tail -f`）でメモリ不足で落ちる
  ことがある**（2-2）と、**`&` を付けるとキーを押してもすぐ止まらない
  ことがある**（2-3）を書いた
- `docs/User.md:250-252` — `Ctrl-C` でもコマンドは止まる（2-1 の結果）
- `docs/User.md:255` — `-d` のログは「長いときは先頭だけ」
- `docs/Developer.md` — アラームのコマンドの節に、
  `ALARM_STOP_SEC` が 3 か所で効くので**最悪 3 秒**（好みの範囲の 1 つ目）、
  `poll()` の確認（2-4）、`Ctrl-C` の後始末（2-1）、`main()` の初期化
  （2-5）、**止められない書き方**（2-3 / 2-2 を直さないと決めたこと）を追記
- `docs/Developer.md` — テストの節に `tests/conftest.py` の安全弁（2-6）と、
  `Ctrl-C` の実機手順の在りかを追記

## 検証（3 巡目）

| コマンド | 結果 |
|---|---|
| `uv run pytest tests` | 188 passed（終了コード 0） |
| `uv run ruff format --line-length 78 src tests` | 25 files left unchanged（0） |
| `uv run ruff check --fix --extend-select I src tests` | All checks passed!（0） |
| `uv run basedpyright src tests` | 0 errors, 0 warnings, 0 notes（0） |
| `uv run mypy src tests` | Success: no issues found in 25 source files（0） |

### `Ctrl-C` の実機確認（指示された完了条件）

`pty.fork()` で疑似端末を作り、その子で
`uv run tmr pomodoro -w 0.02 -c 1 --cmd "sleep 300"` を実行。
`TIME UP` が出た 0.5 秒後に master へ `\x03` を書き込む。手順は次のとおり
（`pty.fork()` の子はセッションリーダーになり、疑似端末が制御端末に
なるので `\x03` が `SIGINT` として届く。`pty.openpty()` +
`subprocess.Popen` では届かないので注意）。

```python
pid, m_fd = pty.fork()
if pid == 0:
    os.execvp("uv", ["uv", "run", "--project", "<repo>", "tmr",
                     "pomodoro", "-w", "0.02", "-c", "1",
                     "--cmd", "sleep 300"])
# 親: TIOCSWINSZ で 100x24 にし（狭いと "!?" しか出ない）、
#     出力に "TIME UP" が出たら os.write(m_fd, b"\x03")
```

結果:

| | 修正前 | 修正後 |
|---|---|---|
| `Ctrl-C` から終了まで | （残骸が残る） | **0.08 秒** |
| `Aborted.` の表示 | 出る | 出る（変わらず） |
| `pgrep -af "sleep 300"` | `/bin/sh -c sleep 300` と `sleep 300` が残った | **無し** |

プロセスの確認は `pgrep` で PID を見てから `kill` した（`pkill` は使っていない）。

`[Q]` の経路も再確認（`--cmd "sleep 300"`）: キーから 0.07 秒で終了、
残骸なし。

## 残る懸念

- **2-3（`&` で孫がパイプを握る形）は直していない。** 指示どおり
  `docs/User.md` に注意を書いただけなので、`--cmd "aplay foo.wav &"` の
  ような書き方をすると、キーを押してもコマンドが終わるまで `main()` が
  返らない（`stop_alarm_cmd()` の docstring が言う「True なら
  `join()` してよい」の約束は、この場合だけ守られない）
- **2-2（大量出力で OOM）も現状のまま。** ログに出す長さは 200 文字に
  切り詰めたが、`communicate()` が溜め込む分は変わらない
- `poll()` は `stop_alarm_cmd()` と `kill_alarm_cmd()` の 2 か所で
  呼ぶが、その間にアラームのスレッドが `communicate()` で子を回収する
  可能性は残る（窓は狭くなったが消えていない。2-4 の指摘どおり）

---

# 追記: 3 巡目レビューへの対応（4 巡目）

3-1（2 度目の `Ctrl-C`）と 3-2（`docs/User.md` の `&` の書きぶり）だけ直した。
3-3 / 3-4 / 3-5 / 3-6 は対応不要の判断に従い、触っていない。

## 3-1. 2 度目の `Ctrl-C` で子が残る

**reviewer の案（`try/except KeyboardInterrupt: pass` で包む）だけでは
直らなかった**（実機で確認）。段階を踏んだので経緯を残す。

1. まず案どおり `except` 節の中を `try/except KeyboardInterrupt: pass` で
   包んだ。→ **残骸は消えなかった。** 2 度目の割り込みは
   `stop_alarm_cmd()` の途中（`SIGTERM` の後の `join()`）で飛ぶので、
   捕まえて握り潰すと**そのまま後始末を打ち切ってしまい**、
   `SIGKILL` に進まない
2. 次に後始末の間だけ `signal.pthread_sigmask()` で `SIGINT` を止めた。
   → **まだ残った。** ログを見ると `KeyboardInterrupt (again)` が出ていた。
   `SIGINT` はプロセス宛てなので、**マスクしていない
   アラームのスレッドが受け取り**、その結果メインスレッドで
   `KeyboardInterrupt` が上がる（マスクは受け取るスレッドを選ぶだけで、
   スレッドが 1 つでも空いていれば素通りする）
3. **アラームのスレッドも `SIGINT` を止めた状態で起動する**ようにして、
   ようやく消えた。スレッドは生成時のマスクを継ぐので、
   `ring_alarm()` で `thr.start()` を挟む形にした

変更:

- `timer.py:247-249, 251-276` — `main()` の `except` から
  `cleanup_by_interrupt()` を呼ぶ形にした。後始末の間は
  `signal.pthread_sigmask(SIG_BLOCK, {SIGINT})` で `SIGINT` を止め、
  `finally` で戻す。押される前に届いていた分に備えて
  `except KeyboardInterrupt` も残した（2 の段階の実装）
- `timer.py:570-580` — `ring_alarm()` で、`SIGINT` を止めてから
  `thr.start()`、`finally` で戻す（3 の段階。理由をコメントに書いた）
- `tests/test_timer.py` — `test_ring_alarm_blocks_sigint_for_thread`
  （`SIG_BLOCK` → `start()` → `SIG_UNBLOCK` の順）を追加。
  既存の `test_main_keyboard_interrupt_twice`
  （`stop_alarm_cmd` が `KeyboardInterrupt` を投げても後始末を続ける）は
  そのまま通る

### 実機での確認（`pty.fork()`。手順は 3 巡目の節と同じ、`-d` 付き）

`--cmd "trap '' TERM; sleep NNN"`（`SIGTERM` を無視するコマンド）で、
`TIME UP` の 0.5 秒後に `Ctrl-C`、その 0.3 秒後にもう 1 度。

| | 修正前 | 修正後 |
|---|---|---|
| `Ctrl-C` 1 回（`sleep`） | 残骸なし | 残骸なし（0.05 秒） |
| `Ctrl-C` 1 回（TERM 無視） | 残骸なし | 残骸なし（1.05 秒。`SIGKILL` まで進む） |
| **`Ctrl-C` 2 回（TERM 無視）** | **`/bin/sh` と `sleep` が残った** | **残骸なし**（ログに `SIGTERM` → `SIGKILL` の 2 行。`KeyboardInterrupt (again)` は出ない） |

`[Q]` の経路（`--cmd "sleep NNN"`）も再確認: キーから 0.05 秒で終了、残骸なし。
残ったプロセスの確認は `pgrep` → PID 指定の `kill` で行った（`pkill` は不使用）。

## 3-2. `docs/User.md` の `&` の注意

- `docs/User.md:270-274` — 「そのプロセスがすぐには止まらない」から、
  **「キーを押しても止められず、そのコマンドが終わるまで tmr 自体が
  止まって見えます（画面が変わらず、ポモドーロなら次のフェーズにも
  進みません）」**に書き直した。`docs/Developer.md` 側の説明と揃えた

## 文書（併せて直したもの）

- `docs/Developer.md` — アラームのコマンドの節に、後始末の間 `SIGINT` を
  止めること、アラームのスレッドも `SIGINT` を止めて起動すること、
  その理由（マスクを素通りする）を追記

## 検証（4 巡目）

| コマンド | 結果 |
|---|---|
| `uv run pytest tests` | 190 passed（終了コード 0） |
| `uv run ruff format --line-length 78 src tests` | 25 files left unchanged（0） |
| `uv run ruff check --fix --extend-select I src tests` | All checks passed!（0） |
| `uv run basedpyright src tests` | 0 errors, 0 warnings, 0 notes（0） |
| `uv run mypy src tests` | Success: no issues found in 25 source files（0） |

## 残る懸念

- `signal.pthread_sigmask` は POSIX 専用（`killpg` と同じ前提。
  2-7 の判断どおり Windows は想定しない）
- `SIG_UNBLOCK` は元のマスクを見ずに解除する。tmr を組み込んだ側が
  `SIGINT` を止めていた場合、`ring_alarm()` / `cleanup_by_interrupt()` の
  後に解除された状態になる。CLI では起こらない

---

# 追記: 4 巡目レビューへの対応（5 巡目）

4-1（子がマスクを継ぐ）は文書に 1 行、4-3（マスクのテストの順序）は
テストを書き直した。4-2 と「好みの範囲」の 2 件目、
2-2 / 2-3 / 2-7、3 巡目の「検討」4 件は対応不要の判断に従い触っていない。

## 4-1. コマンドが `SIGINT` を止めた状態で起動される（文書のみ）

- `docs/Developer.md` — アラームのコマンドの節に、
  「その副作用で**アラームのコマンド自身も `SIGINT` を止めた状態で
  起動する**（`Popen` をアラームのスレッドから呼ぶので、子がマスクを
  継ぐ）。tmr は `SIGTERM` / `SIGKILL` で止めるので停止手順には
  影響せず、そのままにしている」と書いた
- 併せて、「好みの範囲」の 1 件目（**解除ではなく元のマスクへ戻す理由**）も
  同じ箇所に 1 行足した（呼ぶ側が `SIGINT` を止めていることがあるため）

コードは変えていない。

## 4-3. マスクのテストが順序を見ていない

`unittest.mock` の `attach_mock()` で 1 つの親モックにまとめ、
`manager.mock_calls` の**名前の並び**で順序を固定した。

- `tests/test_timer.py: test_ring_alarm_blocks_sigint_for_thread`
  — `tmr.timer.threading.Thread` も patch して親にまとめ、
  `["Thread", "mask", "Thread().start", "mask"]` を assert。
  **`start()` がマスクの内側で起きること**が固定された
  （元のマスクへ戻す `call_args_list` の assert も残した）
- `tests/test_timer.py: test_cleanup_by_interrupt_restores_sigmask`
  — `Timer.stop_alarm_cmd` を patch して親にまとめ、
  `["mask", "stop", "mask"]` を assert。`stop_alarm_cmd()` に
  `alarm_thr` が渡ることも見る形にした
  （`mock_subprocess` / `mock_killpg` は不要になったので外した）

### 効いていることの確認

`ring_alarm()` の `thr.start()` を**マスクの外へ出す**改変を入れて
テストを流し、`test_ring_alarm_blocks_sigint_for_thread` が
落ちることを確かめた（`1 failed, 55 passed`）。確認後、
コードは元に戻してある（`git diff` に改変は残っていない）。

## 検証（5 巡目）

| コマンド | 結果 |
|---|---|
| `uv run pytest tests` | 191 passed（終了コード 0） |
| `uv run ruff format --line-length 78 src tests` | 25 files left unchanged（0） |
| `uv run ruff check --fix --extend-select I src tests` | All checks passed!（0） |
| `uv run basedpyright src tests` | 0 errors, 0 warnings, 0 notes（0） |
| `uv run mypy src tests` | Success: no issues found in 25 source files（0） |

実機での再確認はしていない（コードを変えていないため）。

## 残る懸念

- 4-2（`SIG_BLOCK` から `try:` に入るまでの窓）は対応不要の判断どおり
  そのまま。CLI では実害無し、ライブラリ経路でのみ
  「`SIGINT` を止めたまま」が残りうる
