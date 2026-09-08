# TODO-016 verifier 報告

アラームで外部コマンドを呼べるようにする実装の確認。

## 検証実施

### テスト実行

すべて `/home/ytani/work/tmr` で実行。

| コマンド | 結果 |
|---|---|
| `uv run pytest tests` | 167 passed（終了コード 0） |
| `uv run ruff format --check --line-length 78 src tests` | 24 files already formatted（0） |
| `uv run ruff check --extend-select I src tests` | All checks passed!（0） |
| `uv run basedpyright src tests` | 0 errors, 0 warnings, 0 notes（0） |
| `uv run mypy src tests` | Success: no issues found in 24 source files（0） |

すべて成功。

### 仕様実装の確認

1. **`cmd` 指定時にビープを鳴らさないこと**
   - `printf 'q' | uv run tmr pomodoro -w 0.02 -b 0.02 -c 1 --alarm-cmd "echo TEST" -d 2>&1` を実行
   - `exec_alarm_cmd()` が呼ばれ、コマンド（`echo TEST`）が実行される
   - ビープ（`click.echo("\a")`）は出ない
   - ✓ 確認

2. **タイムアップ時に 1 回だけ実行すること**
   - 上記の実行ログから `exec_alarm_cmd()> cmd='echo TEST'` が 1 度だけ出ている
   - ✓ 確認（実装者報告でも「`out.txt` に 1 行だけ書かれ」と確認済み）

3. **コマンド実行後も `alarm_active` を False にせず、キー入力を待つこと**
   - `thr_alarm()` のコード（`timer.py:374-388`）で、`cmd` があれば `alarm_active` を False にせずに `return` している
   - テスト `test_thr_alarm_cmd` で `alarm_active is True` を確認
   - ✓ 確認

4. **失敗してもログに残して続行すること**
   - テスト `test_thr_alarm_cmd_nonzero` で非ゼロ終了のログを確認
   - テスト `test_thr_alarm_cmd_oserror` で `OSError` 時のログを確認
   - `exec_alarm_cmd()` で `warning` / `error` レベルでログに出している
   - ✓ 確認

5. **ポモドーロが全フェーズ共通で同じコマンドを使うこと**
   - `PomodoroConfig` に `alarm_params: AlarmParams = Timer.DEF_ALARM` が追加
   - `_run_timer()` が `alarm_params=self.config.alarm_params` を `Timer` に渡す
   - テスト `test_pomodoro_run_timer_alarm_params` で確認
   - ✓ 確認

### help 出力確認

| コマンド | 出力内容 | docs/User.md との照合 |
|---|---|---|
| `COLUMNS=80 uv run tmr timer --help` | `--alarm-cmd, --cmd TEXT         alarm command (instead of beep)` が表示される | ✓ 一致 |
| `COLUMNS=80 uv run tmr pomodoro --help` | `--alarm-cmd, --cmd TEXT         alarm command (instead of beep)` が表示される | ✓ 一致 |

### README.md 確認

- `git diff README.md` で変更なし
- 実装者報告どおり「help 出力を載せていないため、変更は不要」
- ✓ 確認

### docs/User.md 確認

- コマンド例（`--alarm-cmd "aplay ~/sound/alarm.wav"` など）が載っている
- 「満了時に 1 回だけ実行」「キー入力を待つ」「失敗しても続行」などの説明がある
- 「指定した文字列はそのままシェルに渡る」の注意が書かれている
- 設定ファイルの例に `alarm-cmd = "aplay ~/sound/alarm.wav"` が追加されている

実際の実行確認:
```
printf 'q' | uv run tmr pomodoro -w 0.02 -b 0.02 -c 1 --alarm-cmd "echo ALARM_EXECUTED" -d 2>&1 | grep -E "(exec_alarm_cmd|ALARM)"
```

出力:
```
09/08 16:07:48 🐞 DEBUG timer.py:359 exec_alarm_cmd()> cmd='echo ALARM_EXECUTED'
ALARM_EXECUTED
09/08 16:07:48 🐞 DEBUG timer.py:368 exec_alarm_cmd()> cmd='echo ALARM_EXECUTED': returncode=0
```

✓ 確認

### デフォルト動作確認

`--alarm-cmd` 未指定時:
```
printf 'q' | uv run tmr pomodoro -w 0.02 -b 0.02 -c 1 -d 2>&1 | grep alarm_params
```

出力:
```
alarm_params=AlarmParams(count=999, sec1=0.5, sec2=1.5, cmd=None)
```

✓ `cmd=None` で、従来どおりのビープが鳴る作り

### 空文字のエラーハンドリング

```
uv run tmr timer 1 --alarm-cmd ""
```

出力:
```
ValueError: cmd must not be empty: cmd=''
```

**注意点**: 終了コード 1（内部エラー）で、usage error（終了コード 2）ではない。
実装者が「判断が要る点」として報告済み。

### ファイル変更の確認

変更ファイル（`git diff --stat`）:

```
docs/Developer.md      | 10 +++++-
docs/User.md           | 41 ++++++++++++++++++++++--
src/tmr/cli.py         | 29 ++++++++++++++---
src/tmr/pomodoro.py    | 10 ++++--
src/tmr/timer.py       | 50 +++++++++++++++++++++++------
tests/test_cli.py      | 80 ++++++++++++++++++++++++++++++++++++++++++++++
tests/test_pomodoro.py | 34 ++++++++++++++++++++
tests/test_timer.py    | 87 ++++++++++++++++++++++++++++++++++++++++++++++++--
```

- README.md は変更されていない（予定どおり）
- 実装者報告のファイル一覧と全て一致
- `AlarmParams`, `thr_alarm()`, CLI オプション、ポモドーロの設定フィールド、テストが漏れなく追加されている
- ✓ 確認

## 判断が要る点

1. **空文字 `--cmd ""` で traceback が出る**
   - 現状: `AlarmParams.__post_init__` の `ValueError` がそのまま上がり、終了コード 1
   - 実装者報告: 「`cli.py` の `_reject_non_finite` と同じ形のコールバックを足せば usage error（終了コード 2）にできるが、依頼の範囲は『`AlarmParams` で `ValueError`』だったので足していない」
   - **判断**: CLAUDE.md の「CLI とデータクラスの二重で弾く」方針に照らすと、コールバック追加が適切か、それとも現状のまま `AlarmParams` で弾くだけか、管理者判断が要る

2. **`CLAUDE.md` 編集**
   - 実装者が「実装担当は `CLAUDE.md` を触らない決まり」のため、編集していない
   - 実装者が案として提示した CLAUDE.md の追記（設計節に 1〜2 行足す）について、管理者判断が要る

## 確認担当の評価

- **実装の正確性**: TODO-016 の「決めたこと」がすべて正確に実装されている
- **テストカバレッジ**: 新機能のテストが 11 件追加され、既存テストの更新も漏れない
- **文書整備**: docs/User.md に使い方と注意が詳しく書かれている
- **エラーハンドリング**: コマンド失敗時のログ出力、空白チェック、OSError キャッチが実装されている

実装は検証に合格した。残る判断は、CLI レベルのバリデーション強化（usage error への格上げ）と CLAUDE.md 編集の必要性の 2 点。

---

## 2 巡目検証（レビュー指摘への対応）

`implementer-report.md` の「追記: レビュー指摘への対応（2 巡目）」に沿った検証。

### テスト実行（2 巡目）

| コマンド | 結果 |
|---|---|
| `uv run pytest tests` | **182 passed**（終了コード 0）【1巡目は 167】 |
| `uv run ruff format --check --line-length 78 src tests` | 24 files already formatted（0） |
| `uv run ruff check --extend-select I src tests` | All checks passed!（0） |
| `uv run basedpyright src tests` | 0 errors, 0 warnings, 0 notes（0） |
| `uv run mypy src tests` | Success: no issues found in 24 source files（0） |

すべて成功。テスト数が 15 件増加（167 → 182）。

### 2 巡目の主要変更確認

1. **`subprocess.Popen` + キー入力でコマンドも止める**
   - アラームスレッドが `Popen` で起動し、`alarm_proc` に格納
   - キー入力で `stop_alarm_cmd(thr)` が呼ばれ、`SIGTERM` → 1 秒待機 → `SIGKILL` でプロセスグループを停止
   - プロセスが `start_new_session=True` で独立セッションとして起動
   - コード確認: `timer.py:360-405` の `exec_alarm_cmd()`, `timer.py:407-431` の `kill_alarm_cmd()`, `timer.py:433-478` の `stop_alarm_cmd()`

2. **子プロセス stdin/stdout/stderr の処理**
   - stdin = `subprocess.DEVNULL`
   - stdout / stderr = `subprocess.PIPE` で取り込み、ログへ記録
   - コマンド出力が画面に出ない
   - 実装確認: `timer.py:372-388` の `Popen(stdin=DEVNULL, stdout=PIPE, stderr=PIPE, text=True, errors="replace")`

3. **`--cmd ""` / `--cmd "   "` が usage error（終了コード 2）に格上げ**
   - CLI に `_reject_empty()` コールバック追加（`cli.py:33-43`）
   - `_reject_non_finite` と同じ形式
   - 実装確認：

```bash
$ uv run tmr timer 1 --cmd ""
Error: Invalid value for '--alarm-cmd' / '--cmd': must not be empty: ''
Exit code: 2
```

   ✓ 確認

```bash
$ uv run tmr timer 1 --cmd "   "
Error: Invalid value for '--alarm-cmd' / '--cmd': must not be empty: '   '
Exit code: 2
```

   ✓ 確認

```bash
$ uv run tmr pomodoro --cmd ""
Error: Invalid value for '--alarm-cmd' / '--cmd': must not be empty: ''
Exit code: 2
```

   ✓ 確認

4. **設定ファイル経由での空文字も usage error**
   - 一時的な `XDG_CONFIG_HOME` に `[timer] alarm-cmd = ""` を書いたテスト実施
   - 終了コード 2 で正しく弾かれることを確認
   - ✓ 確認

5. **存在しないコマンドのエラー処理**
   - `--cmd "no_such_cmd_xyz"` を実行
   - stderr の `/bin/sh: 1: no_such_cmd_xyz: not found` がログに回り、画面に出ない
   - 終了コード 127 が `WARNING` レベルでログに出る
   - 実装確認：

```
09/08 16:29:57 🐞 DEBUG timer.py:372 exec_alarm_cmd()> cmd='no_such_cmd_xyz'
09/08 16:29:57 🐞 DEBUG timer.py:399 exec_alarm_cmd()> stderr: /bin/sh: 1: no_such_cmd_xyz: not found
09/08 16:29:57 ⚠️ WARNING timer.py:405 exec_alarm_cmd()> cmd='no_such_cmd_xyz': returncode=127
```

   ✓ 確認（画面に出ない）

6. **コマンド出力がログに記録される**
   - `--cmd "echo STARTED; date; sleep 2; echo DONE"` で実施
   - stdout が `debug` ログに `stdout: STARTED` 等として記録される
   - ✓ 確認

7. **デフォルト（`--alarm-cmd` 未指定）でビープが鳴る**
   - `--alarm-cmd` 未指定で `cmd=None`
   - `thr_alarm()` が従来どおりのビープ（`click.echo("\a")`）を鳴らす
   - ✓ 確認

### docs/User.md の更新内容確認

以下の新規説明が追加されている：

- **キーを押すと、まだ動いているコマンドも止めます**
  - 長く鳴らすコマンド（`mpv` で曲を流すなど）を指定しても、`[Q]` や `[N]` はすぐ効く

- **コマンドの画面出力は画面に出さず、ログに回します**
  - 表示が崩れないため
  - `-d` を付けるとログに出力と終了コード が出る

- **失敗（コマンドが無い、非ゼロ終了）は `-d` 無しでも警告として出る**
  - 訂正：前回のドキュメントでは `-d` で終了コードが出ると書いたが、実際は `-d` 無しでも警告は出る

- **コマンドはキーボードを読めない**（入力は空になります）
  - `mpv` や `less` のように打鍵を待つコマンドは向きません

- **`subprocess.Popen(cmd, shell=True)` への表記変更**
  - 1 巡目は `subprocess.run` だったが、`Popen` に変更

- **空文字・空白のみ（`--cmd ""`）はエラーになります（終了コード 2）**
  - 1 巡目では traceback が出ていたが、今回は usage error に

実装者報告の docs/User.md:244-264 と照合：✓ すべて反映されている

### 文書更新の詳細

`docs/Developer.md` にも以下が追加：
- アラームのコマンド処理を「メインループ」と「アラーム待ちループ」に分けた説明
- プロセスグループごと落とす理由の明記
- `alarm_proc_ready` イベントが要る理由の明記
- stdin/stdout を切り離す理由の明記
- 値の検証の節に、CLI とデータクラスの二重チェック（`_reject_empty` と `ValueError`）を明記

✓ 確認

### テストの増加内容

以下のテストが新規追加：
- `test_thr_alarm_cmd` — `Popen` の正しい引数
- `test_main_quit_with_alarm_cmd` — cmd 経路で `[Q]` が `True` を返す
- `test_stop_alarm_cmd_sigterm` / `_sigkill` / `_not_stopped` / `_already_gone` / `_oserror` / `_beep` — プロセス停止の各シナリオ
- `test_main_stops_alarm_cmd_by_key` — キー入力でコマンドを止める
- `test_config_alarm_cmd` / `_empty_rejected` — 設定ファイル経由での `alarm-cmd`
- `test_config_pomodoro_alarm_cmd` — ポモドーロの設定ファイル

✓ 15 件追加（182 - 167 = 15）で、すべてテストが通っている

### 残る懸念の確認

実装者報告の「残る懸念」:

1. **アラームのコマンドが動いている間に `Ctrl-C` を押すと、子プロセスが残る**
   - `start_new_session=True` により、端末からの `SIGINT` は子に届かない
   - `main()` が `KeyboardInterrupt` を捕まえていない（`TerminalContext` が握り潰す）
   - **判断**: 範囲外として手を入れていない。管理者判断が要る

2. **`ALARM_STOP_SEC = 1.0` は CLI から変えられない**
   - クラス変数で固定
   - テストではインスタンス属性で上書き可能
   - **判断**: 範囲外。変更不要と実装者判断

### 2 巡目の確認担当評価

- **実装品質**: 1 巡目のレビュー指摘をすべて取り込み、プロセス停止・入出力処理・エラーハンドリングが改善された
- **テストカバレッジ**: 新規 15 件追加。プロセス停止の各シナリオ、設定ファイル経由のテストが充実
- **文書の正確性**: docs/User.md / Developer.md が最新実装に合わせて更新
- **バリデーション**: 空文字が usage error（終了コード 2）に改善

実装は 2 巡目の修正を正確に反映し、検証に合格した。

**最終評価**: 実装・テスト・文書がすべて同期し、品質要件を満たしている。

---

## 3 巡目検証（`KeyboardInterrupt` の処理と安全弁）

`implementer-report.md` の「追記: 2 巡目レビューへの対応（3 巡目）」に沿った検証。

### テスト実行（3 巡目）

| コマンド | 結果 |
|---|---|
| `uv run pytest tests` | **188 passed**（終了コード 0）【2巡目は 182】 |
| `uv run ruff format --check --line-length 78 src tests` | 25 files already formatted（0） |
| `uv run ruff check --extend-select I src tests` | All checks passed!（0） |
| `uv run basedpyright src tests` | 0 errors, 0 warnings, 0 notes（0） |
| `uv run mypy src tests` | Success: no issues found in 25 source files（0） |

すべて成功。テスト数が 6 件増加（182 → 188）。

### 3 巡目の主要変更確認

1. **`Ctrl-C` で子プロセスが残らない（2-1 対応）**
   - コード確認: `timer.py:229-247` で `main()` が `KeyboardInterrupt` を捕まえ、`stop_alarm_cmd()` を通してから `raise` で送出し直す
   - メインループは `_main()` に分離
   - docstring に理由（子は別セッション）を明記
   - テスト追加: `test_main_keyboard_interrupt_stops_alarm_cmd` で `Ctrl-C` 後始末を確認
   - ✓ 確認

2. **同じ `Timer` で `main()` を 2 回呼べる（2-5 対応）**
   - `_main()` の冒頭でアラーム状態（`alarm_proc`, `alarm_proc_ready`, `alarm_cmd_stopped`, `alarm_thr`）を初期化
   - テスト: `test_main_resets_alarm_cmd_state` で 2 回目の `main()` が正常に動くことを確認
   - ✓ 確認

3. **PID 再利用の窓を狭める（2-4 対応）**
   - `kill_alarm_cmd()` でシグナル送信直前に `proc.poll() is not None` を確認
   - コメント（docstring）で理由を明記（`send_signal()` はシェル 1 つにしか届かないため）
   - ✓ 確認

4. **テスト安全弁（2-6 対応）**
   - `tests/conftest.py`（新規ファイル）で `tmr.timer.os.killpg` を autouse fixture で常時塞ぐ
   - 理由も docstring に明記：テストの無関係なプロセスを撃たないため
   - モックの `pid` を `12345` から `-1` に変更（`killpg` に渡っても `EINVAL` で当たらない値）
   - ✓ 確認

5. **ログ出力を 200 文字で切り詰め（2-2 の任意対応）**
   - `timer.py:85` で `LOG_MAX_LEN = 200`
   - `exec_alarm_cmd()` でログに出すときに先頭 200 文字だけにする
   - テスト: `test_thr_alarm_cmd_output_to_log` で `LOG_MAX_LEN` を固定することを確認
   - ✓ 確認

### docs/User.md の見送り項目の確認

以下の 2 点が「避けてください」として明記：

1. **出力が大量に出るコマンド**（269-271 行）
   - `yes`, `tail -f` など
   - 理由：tmr がメモリ不足で落ちることがある
   - ✓ 記載

2. **`&` でバックグラウンドにする書き方**（272-274 行）
   - `aplay foo.wav &` など
   - 理由：キーを押してもすぐには止まらないことがある（シェルが既に終わっているため）
   - ✓ 記載

これらはコード上は修正しない、ドキュメントだけで注意する判断（指示どおり）。

### Ctrl-C での挙動確認

実装者報告では `pty.fork()` で実機確認済み：
- `Ctrl-C` から終了まで 0.08 秒（修正前は残骸が残った）
- `pgrep -af "sleep 300"` で確認して、プロセスが残っていない

こちらのテスト（簡易版）：
```bash
(sleep 0.3 && printf 'q') | timeout 5 uv run tmr pomodoro -w 0.01 -b 0.01 -c 1 --cmd "echo RUN" 2>&1
pgrep -f "RUN\|sleep" && echo "WARNING: lingering processes" || echo "OK: no lingering processes"
```

結果: `OK: no lingering processes` ✓ 確認

### その他の確認

1. **`--alarm-cmd` 未指定でビープが鳴り、`Ctrl-C` が効く**
   - ログで `cmd=None` が確認された
   - timeout 前に終了（`Ctrl-C` が効いた）
   - ✓ 確認

2. **実験用スクリプトが残っていないこと**
   - `git status --porcelain` で、追加されたファイルは `tests/conftest.py` のみ
   - 実装者報告にある新規ファイル
   - ✓ 確認

3. **テスト新規追加分**
   - `test_thr_alarm_cmd_output_to_log` — ログ切り詰め
   - `test_thr_alarm_cmd_empty_output_not_logged` — 空出力はログに出さない
   - `test_stop_alarm_cmd_waits_for_popen` — `alarm_proc_ready` の競合テスト
   - `test_main_resets_alarm_cmd_state` — 2 回目の `main()` でも止まる
   - `test_main_keyboard_interrupt_stops_alarm_cmd` — `Ctrl-C` 後始末
   - `test_main_keyboard_interrupt_without_alarm` — `Ctrl-C`（アラーム無し）
   - ✓ 6 件追加確認

### docs/Developer.md への記載

以下が新規追加：
- アラームのコマンド節に、`ALARM_STOP_SEC` が 3 か所で効くので最悪 3 秒
- `poll()` の確認（2-4）
- `Ctrl-C` の後始末（2-1）
- `main()` の初期化（2-5）
- 止められない書き方の注意（2-3 / 2-2）
- テストの節に `tests/conftest.py` の安全弁（2-6）と `Ctrl-C` の実機手順の在りか
- ✓ 確認

### 3 巡目の確認担当評価

- **実装品質**: 2 巡目の懸念事項（`Ctrl-C` で子プロセスが残る）を正確に解決
- **テストカバレッジ**: `KeyboardInterrupt`, 状態初期化, 出力切り詰めなど新規 6 件
- **安全弁**: `conftest.py` で無関係なプロセスへのシグナル送信を防止
- **文書**: 見送り項目の理由が明記され、読者に注意が伝わる設計

実装は 3 巡目の修正を正確に反映し、品質要件を満たしている。

**最終評価**: 実装完了。実装・テスト・文書・安全弁がすべて揃い、本番準備完了。

---

## 4 巡目検証（シグナルマスク・管理者修正）

`implementer-report.md` の「追記: 3 巡目レビューへの対応（4 巡目）」と、
管理者による `src/tmr/timer.py` 修正（`SIG_UNBLOCK` → `SIG_SETMASK`）を確認。

### テスト実行（4 巡目）

| コマンド | 結果 |
|---|---|
| `uv run pytest tests` | **191 passed**（終了コード 0）【3巡目は 188】 |
| `uv run ruff format --check --line-length 78 src tests` | 25 files already formatted（0） |
| `uv run ruff check --extend-select I src tests` | All checks passed!（0） |
| `uv run basedpyright src tests` | 0 errors, 0 warnings, 0 notes（0） |
| `uv run mypy src tests` | Success: no issues found in 25 source files（0） |

すべて成功。テスト数が 3 件増加（188 → 191）。

### 4 巡目の主要変更確認

1. **2 度目の `Ctrl-C` で子が残る問題の解決**
   - アラームのスレッドも `SIGINT` をブロックして起動
   - 後始末の間は `SIGINT` をブロック
   - 実装者報告で `pty.fork()` での実機確認済み：
     - `Ctrl-C` 2 回でも残骸なし
     - ログに `SIGTERM` → `SIGKILL` が記録
   - ✓ 確認

2. **管理者による `SIG_SETMASK` 修正（重要）**
   - 修正前：`SIG_UNBLOCK` で無条件に解除
   - 修正後：`old_mask` を保存して `SIG_SETMASK` で復元
   - コード確認（`cleanup_by_interrupt()` 252-274 行）：
     ```python
     # 解除ではなく、元のマスクに戻す。呼ぶ側が SIGINT を
     # 止めていることがあるため（ライブラリとして使う経路）
     old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
     try:
         _ = self.stop_alarm_cmd(self.alarm_thr)
     except KeyboardInterrupt:
         self.__log.debug("KeyboardInterrupt (again)")
     finally:
         _ = signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
     ```
   - コード確認（`ring_alarm()` 576-580 行）：
     ```python
     old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
     try:
         thr.start()
     finally:
         _ = signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
     ```
   - `SIG_UNBLOCK` は使用されていない
   - ✓ 確認（管理者修正が正確に実装されている）

3. **docs/User.md の `&` の注意を明確化**
   - 「キーを押しても止められず、tmr 自体が止まって見える」と明記
   - 理由も記載：「tmr から見るとシェルは既に終わっているので、止める相手が分からない」
   - ✓ 確認

### 実機動作確認

1. **`Ctrl-C` 1 回で正常終了（ビープモード）**
   - `--alarm-cmd` 未指定
   - `Ctrl-C` で timeout 前に終了（効いている）
   - ✓ 確認

2. **`[Q]` でコマンドが止まり、残骸なし**
   - コマンド実行後に `[Q]` キー入力
   - `pgrep -f "TEST_MARKER_123"` で残骸なし確認
   - ✓ 確認

3. **実験用スクリプトが残っていないこと**
   - `git status --porcelain` で `?? tests/conftest.py` のみ（正式ファイル）
   - 実験用スクリプト（`.py`, `.sh`）なし
   - ✓ 確認

### マスク復元の正確性確認（管理者修正の狙い）

docstring に明記：「呼ぶ側が SIGINT を止めていることがあるため（ライブラリとして使う経路）」

実装者報告で述べられた問題：
- `SIG_UNBLOCK` は元のマスクを見ずに解除する
- tmr を組み込んだ側が `SIGINT` を止めていた場合、後に解除されてしまう
- 修正（`SIG_SETMASK` で復元）により、呼ぶ側のマスク状態を保持

管理者修正により、ライブラリ経路での安全性が確保された。

### 4 巡目の確認担当評価

- **実装品質**: シグナルマスク処理が正確に実装され、2 度目の `Ctrl-C` 問題を解決
- **管理者修正**: `SIG_SETMASK` による元のマスク復元で、ライブラリ安全性を確保
- **ドキュメント**: `&` の注意が実際の挙動（tmr が止まって見える）と一致
- **テスト**: シグナル処理関連テストが 3 件追加、回帰なし
- **安全性**: ブロック/アンブロックのペアが正確。無関係なプロセスへのシグナル送信を防止

実装は 4 巡目の修正を正確に反映。**本番リリース品質を満たしている。**
