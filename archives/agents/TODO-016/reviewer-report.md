# TODO-016 reviewer 報告

対象: 未コミットの `git diff`（`src/tmr/{cli,pomodoro,timer}.py`,
`docs/{User,Developer}.md`, `tests/*`）。コードは直していない。

根拠の種別は各項に付けた（**実測** / コードの該当行 / `CLAUDE.md` の記述）。
実測は `Terminal` と `TimerView` をモックした短いスクリプトで
`Timer.main()` を動かし、時間を測って確かめた。

---

## 要修正

### 1. `src/tmr/timer.py:280` — コマンドが終わるまで `main()` が返らない

`thr.join()` に上限が無いので、**キーを押してアラームを止めたあとも、
コマンドが終わるまでプロセスが固まる**。

実測（`t_limit=0.2`、`--cmd "sleep N"` 相当）:

| 押したキー | cmd | `main()` の所要 | 戻り値 |
|---|---|---|---|
| `KEY_ENTER` | `sleep 3` | 3.21 秒 | False |
| `Q` | `sleep 2` | 2.20 秒 | True |
| `Q` | `true` | 0.20 秒 | True |

問題になる点:

- ポモドーロで `[Q]` を押しても、コマンドが終わるまで終了しない
  （`sleep 2` で 2.2 秒。`mpv` で曲を最後まで鳴らす設定なら曲の長さ分）。
  利用者からは「`Q` が効かない」ように見える
- 次のフェーズも同じだけ遅れる（`_run_timer()` が返らないため）
- このとき `with self.term.cbreak()` は既に抜けている
  （`timer.py:262-269` の外）。つまり**待っている間の打鍵は端末に
  エコーされ、バッファに残ったままシェルに渡る**
- `docs/Developer.md:250` の「メインループは止まりません」は、
  アラームの待ちループの間だけの話。この最後の `join()` には触れて
  いないので、読むと止まらないように受け取れる

`join()` 自体は今回の変更前からあるが、ビープのときは
`alarm_active` が False になれば次の `time.sleep()` に入らないので
すぐ返っていた（`timer.py:382-388`）。cmd の経路で初めて
「外部プロセスの実行時間」がそのまま待ち時間になった。

補足（実測）: `join()` 中の `Ctrl-C` は割り込めて、`TerminalContext` が
握り潰して `Aborted.` を出す。ただし**子プロセスは生き残り、tmr の終了後も
端末に出力を書いた**（`sleep 5; echo ... >&2` で確認）。実際の端末では
`Ctrl-C` はフォアグラウンドのプロセスグループ全体に届くので子も死ぬのが
普通だが、そこは **未確認**（tty が要るため）。

案（どれを採るかは管理者判断）: `join(timeout=…)` にする／待ちループの
中で `thr.is_alive()` も見る／`subprocess.Popen` + `terminate()` に
する／少なくとも `docs/User.md` に「コマンドが終わるまで終了しない」と
書く。

### 2. `src/tmr/cli.py:88-94, 167-173` — CLI 側の検証が無く、`--cmd ""` が traceback になる

`CLAUDE.md`「設計」の値の検証の節（`docs/Developer.md:188-198` も同じ）は
**CLI（`click` の型 + コールバック）とデータクラスの二重で弾く**と決めて
いる（TODO-012）。`--alarm-cmd` には `_reject_non_finite` に相当する
コールバックが無く、1 枚目が欠けている。

実測:

```
$ uv run tmr timer 1 --cmd ""
... ValueError: cmd must not be empty: cmd=''   （traceback、終了コード 1）
$ uv run tmr pomodoro --cmd "  "
... 同じ traceback
```

さらに**設定ファイル経由でも同じ traceback**になる（実測。
`XDG_CONFIG_HOME` を切り替え、`[timer] alarm-cmd = ""`）。これは
`CLAUDE.md`「設定ファイル」の**壊れていれば `ClickException` で終了する**に
反する。`--alarm-count -1` などは usage error（終了コード 2）で揃って
いるので、ここだけ揃っていない。

案: `_reject_non_finite` と同じ形の `_reject_empty`（`value` が None なら
素通し、`strip()` が空なら `click.BadParameter`）を両コマンドに付ける。
`AlarmParams.__post_init__` の `ValueError` はライブラリ経路用として残す
（それが二重の作りの意図）。

### 3. `tests/test_cli.py:216-224` — 現状の traceback をテストで固定している

```python
assert isinstance(result.exception, ValueError)
```

指摘 2 を直すと必ず落ちる書き方。仕様として「usage error にする」と
決めるなら `result.exit_code == 2` と `"Usage"` を見る形に変える。
現状のまま（`ValueError`）で行くと決めるなら、なぜ他のオプションと
揃えないのかを `docs/Developer.md` の値の検証の節に 1 行残すべき。
また、ポモドーロ側の `--cmd ""` と、設定ファイル経由の空文字には
テストが無い。

### 4. `CLAUDE.md` の設計の記述が実装とずれた

いずれも `CLAUDE.md`（プロジェクト）の現行の記述。**設計の正はこちら**
なので、実装に合わせて直す必要がある（実装担当は触らない決まりなので
残っている）。

- 「アラームの鳴らし方は `AlarmParams(count, sec1, sec2)`」
  — フィールドが 4 つになった
- 「停止の合図は `alarm_active` フラグ 1 つ（スレッド側もメインループ側も
  見ている）」 — cmd の経路ではスレッド側は一切見ない
  （`timer.py:376-380`）。止まる条件はキー入力だけになった。
  ここは今回の変更でいちばん設計が動いた所なので、1 行では足りない
- 値の検証の節（「二重の作り」）— `cmd` は 1 枚だけ（指摘 2）

`docs/Developer.md` 側は加筆済み（`Developer.md:248-254`）なので、
`CLAUDE.md` は短い追記でよい。

---

## 検討

### 5. 子プロセスが端末（stdin / stdout / stderr）をそのまま引き継ぐ

`timer.py:362` の `subprocess.run(cmd, shell=True, check=False)` は
リダイレクトを一切指定していない。

- **stdout / stderr が表示に混ざる。** 実測（`-d` 無し）:

  ```
  /bin/sh: 1: no_such_cmd_xyz: not found
  09/08 16:10:24 ⚠️ WARNING timer.py:370 exec_alarm_cmd()> cmd='...': returncode=127
  ```

  どちらもアラーム中の再描画の最中に出るので画面が崩れる。
  `aplay` のように正常時も stderr に書くコマンドは珍しくない
- **`docs/User.md` の「（`-d` を付けると、終了コードがログに出ます）」は
  不正確。** 既定水準は INFO（`mylog.logLevel()`）なので、
  `warning` / `error` は `-d` 無しでも出る（上の実測）
- **stdin も引き継ぐ。** cbreak 中の同じ tty を子と `term.inkey()` が
  取り合う形になり、`mpv` や `less` のようにキーを読むコマンドを指定
  すると打鍵が奪われる／端末の設定を変えられる恐れがある。
  これは**未確認**（tty が要る）。コードから読める範囲の指摘

案: `stdin=subprocess.DEVNULL` を付ける、出力は捨てるか
`capture_output=True` にしてログへ回す、成功時以外のログ水準を見直す、
のいずれか。少なくとも `docs/User.md` の `-d` の書きぶりは直したい。

### 6. テストが押さえていない分岐

「動くか」は verifier が確認済みなので、意味の面で抜けている所だけ。

- **cmd 経路で `[Q]` を押したときに `main()` が True を返す**テストが無い。
  ポモドーロの制御経路（`CLAUDE.md`「戻り値でフェーズを制御する」）が
  新しい分岐で壊れていないことを固定する要のテスト。
  実測では正しく True を返した（指摘 1 の表）が、テストは無い
  （`tests/test_timer.py:378-401` は `KEY_ENTER` で False を見るだけ）
- **`join()` の待ち時間**（指摘 1）を捉えるテストが無い。仕様を決めたら
  `thr_alarm` を遅くして時間を測るテストで固定できる
- 設定ファイルの `alarm-cmd`（`docs/User.md` に例を足した）に
  `tests/test_config.py` のテストが無い。キー名として通ることは実測で
  確認したが、テストは無い。なお設定ファイルに書けるのは `alarm-cmd`
  だけで、別名の `cmd` は「知らないキー」になる（`config.py:56-69` が
  `param.name` しか見ないため）。既存の `--s1` / `--s2` と同じ扱いなので
  作りとしては一貫している

### 7. `src/tmr/cli.py:195` — `dataclasses.replace(Timer.DEF_ALARM, cmd=alarm_cmd)`

動作は正しい（`--cmd` 未指定なら `DEF_ALARM` と等しい。
`tests/test_cli.py` で確認済み）。ただし CLI が `Timer.DEF_ALARM` を
経由して `AlarmParams` を組み立てる形は、`timer` 側（`AlarmParams(...)` を
直に組む）と揃っていない。`PomodoroConfig` に `alarm_cmd: str | None` を
持たせて `PomodoroConfig` の中で `AlarmParams` を作る方が、
`pomodoro.py` の他のフィールド（秒とサイクル数という素の値）とも
揃う。今の形でも破綻はしないので、好みに近い。

---

## 好みの範囲

- `timer.py:376` の `if params.cmd:` は、`__post_init__` が空文字を
  弾いているので `is not None` と等価。意図（「空なら鳴らす」ではなく
  「指定が無ければ鳴らす」）を出すなら `is not None` の方が読みやすい
- `exec_alarm_cmd()` は外から呼ぶ想定が無いが public。既存の
  `thr_alarm` / `ring_alarm` も public なので、これは既存に合わせた形

---

## 問題無しを確認した点

- **戻り値によるフェーズ制御**（`CLAUDE.md`「戻り値でフェーズを制御する」）:
  cmd 経路でも `timer.py:277-278` の判定は変わっておらず、アラーム中の
  `[Q]` で `main()` は True を返す（実測）。`[N]` は False（実測）
- **`alarm_active` の食い違い**: cmd 経路ではスレッド側が触らず、
  メインループ側が `timer.py:263-271` で False にする。二重書き込みが
  無くなる方向なので競合は増えていない（記述のずれは指摘 4）
- **ログ**: `exec_alarm_cmd()` は `self.__log`（クラス本体の
  `__log = getLogger(__qualname__)`）を使っており規約どおり
- **`thr_alarm(params)` への引数まとめ**: `ring_alarm()` の
  args 展開が消えて素直になった。呼び出し元は `ring_alarm` とテストだけ
- **help 出力と `docs/User.md`**: 実際の `--help` と 1 文字違わず一致
  （`tmr timer --help` / `tmr pomodoro --help` で照合）
- **README.md**: help 出力を載せていないので変更不要（TODO-016 の
  チェック項目は「該当なし」で満たされている）
- **範囲**: 指示に無い変更は見当たらない
- **コメント**: `timer.py:377-378` の「キー入力を待つため、`alarm_active`
  は False にしない」は「なぜ」を書けている

---

# 2 巡目（`subprocess.Popen` + `killpg` への作り替えのレビュー）

対象: `archives/agents/TODO-016/implementer-report.md` の
「追記: レビュー指摘への対応（2 巡目）」と、現在の `git diff`。

1 巡目で「問題無し」と書いた点の再確認はしていない。以下は
**2 巡目で新たに入った作り**についての指摘。実測は再現手順を添えた
（スクリプトは `/tmp/.../scratchpad/` に置いたので残っていない可能性がある。
手順を書いたので追試できる）。

---

## 要修正

### 2-1. `Ctrl-C` で子プロセスが残るのは、**2 巡目で新しく生じた**（実測）

`timer.py:386-388` の `start_new_session=True` により、子は新しい
セッション（＝新しいプロセスグループ、制御端末なし）に移った。その結果、
**端末が `Ctrl-C` で送る `SIGINT` はフォアグラウンドのプロセスグループ
＝ tmr にしか届かず、子には届かない**。`main()` は
`KeyboardInterrupt` を捕まえないので `stop_alarm_cmd()`（`timer.py:289`）は
走らず、`TerminalContext.__exit__`（`terminal.py:26-29`）が握り潰して
そのまま終了する。子は誰にも止められない。

実測 1（現在のコード、疑似端末を作って `Ctrl-C` を送る）:

```
pty.fork() → uv run tmr pomodoro -w 0.02 -b 0.02 -c 1 --cmd "sleep 301"
4.2 秒後に \x03 を書き込む
→ 画面: "Aborted."（tmr は終了コード 0 で終了）
→ pgrep: 「/bin/sh -c sleep 301」と「sleep 301」が生き残った
```

実測 2（原因の切り分け。tmr を使わず、`start_new_session` の有無だけ変えた
最小の親子を疑似端末の下で動かし、同じく `\x03` を送った）:

| 形 | 子（`sleep`）の生死 |
|---|---|
| `Popen(..., )`（1 巡目と同じ） | **死んだ**（残骸なし） |
| `Popen(..., start_new_session=True)`（2 巡目） | **生き残った** |

つまり 1 巡目のコードでは `Ctrl-C` は子まで届いており、残骸は出なかった。
実装担当の報告にある「元からある問題」ではなく、**2 巡目で入った回帰**。
1 巡目の報告で私が「未確認」としていた点は、これで確定した。

影響は残骸が残ることだけではない。`stdout` / `stderr` は `PIPE` のまま
誰も読まないので、**残った子が 64KB 以上書くと書き込みで永久にブロック
する**（止まったまま残る）。また新しいセッションなので、端末を閉じた
ときの `SIGHUP` も届かない（こちらは **未確認**）。

案（管理者判断）: `main()` で `KeyboardInterrupt` を捕まえて
`stop_alarm_cmd()` を呼んでから再送出する／`TerminalContext` に
後始末のコールバックを渡す／`atexit` か `try/finally` で
`stop_alarm_cmd()` を通す。いずれにせよ `start_new_session=True` を
やめるのは（`killpg` が使えなくなるので）勧めない。

### 2-2. コマンドの出力を全部メモリにためる（`yes` で OOM kill。実測）

`timer.py:380-381, 395` で `stdout` / `stderr` を `PIPE` にして
`communicate()` で受けている。`communicate()` は**終わるまで全部
メモリに積む**ので、出力の多いコマンドを指定すると青天井になる。

実測（この Raspberry Pi 上）:

| コマンド | 結果 |
|---|---|
| `exec_alarm_cmd("yes")` を 1〜3 秒 | **python が SIGKILL で落ちた**（終了コード 137） |
| `exec_alarm_cmd("yes | head -c 50000000")`（50MB） | 0.22 秒、`ru_maxrss` 31.9 MB → **318.6 MB** |

1 巡目（端末に素通し）では画面が汚れるだけで、メモリは増えなかった。
**「画面に出さない」ための変更が、より重い壊れ方に化けている。**
`--cmd "tail -f ..."` のような書き間違いでも起きる。

さらに `timer.py:397-399` は、受け取った文字列を**丸ごと 1 行の
debug ログに出す**。`-d` を付けて 50MB の出力があれば、それが全部
画面に流れる。

案: `stdout=subprocess.DEVNULL`（ログに残すのは終了コードだけ）／
`PIPE` のまま読み取りに上限を付ける（先頭 N バイトだけ残す）／
ログに出す長さを切り詰める。

### 2-3. 孫がパイプを握る形だと、`[Q]` を押しても `main()` が固まる（実測）

`stop_alarm_cmd()` は `timer.py:453-455` で

```python
proc = self.alarm_proc
if proc is None or proc.poll() is not None:
    return True
```

と、**シェルが既に終わっていれば「止める必要なし」として True を返す**。
呼び出し元は `timer.py:289-290` で `thr.join()`（上限なし）する。
ところがシェルが終わっていても、シェルが `&` で残した孫が
`stdout` のパイプを握っていれば `communicate()` は返らない。

実測（`Terminal` / `TimerView` をモックし、アラームに入って 1 秒後に
`[Q]` を押す）:

| cmd | `main()` の所要（本来 1.2 秒） |
|---|---|
| `sleep 8 &` | **8.21 秒** |

`sleep 5 &` を「アラーム直後」に押した場合は 0.20 秒で返る
（このときは `poll()` がまだ `None` なので `killpg` の経路に入り、
グループごと落ちて助かる）。**押すのが遅いか早いかで結果が変わる**。

`--cmd "xdg-open ~/sound/alarm.wav"` のように、起動したプレイヤーが
`fd` を引き継いだまま親だけ先に終わる形でも同じことが起きる（未確認。
`&` の場合は上のとおり実測で確認した）。

`stop_alarm_cmd()` の docstring（`timer.py:445-446`）は
「True なら `thr.join()` してよい（False なら待つと固まる恐れ）」と
書いているが、この早期 return がその約束を破っている。

案: `poll()` の結果に関わらず `thr.join(timeout=…)` を通す／
早期 return する前にも `thr.is_alive()` を見て、生きていれば
`killpg` を撃つ／2-2 と合わせて `stdout` をパイプにしない
（パイプを握られること自体が無くなる）。

---

## 検討

### 2-4. `os.killpg` に pid 再利用の窓がある

`kill_alarm_cmd()`（`timer.py:424`）は `os.killpg(proc.pid, sig)` を
そのまま送る。`proc.poll()` を見てから送るまでの間に、アラームの
スレッド側の `communicate()` が子を回収（`waitpid`）すると、その pid は
**OS の再利用対象**になる。再利用された pid のプロセスグループへ
`SIGTERM` / `SIGKILL` を撃つ余地が、理屈のうえでは残る。

- CPython の `Popen.send_signal()` は、この事故を避けるために
  `returncode` を見てから送る作りになっている。ここはその保護の外
- 実際に踏む確率は低い（pid が一周する必要がある）。ただし相手が
  `SIGKILL` で、無関係なプロセスグループ全体なので、当たったときの
  被害は大きい
- 現に `SIGKILL` の周回で `ProcessLookupError`（＝もう居ない）になる
  経路は実測で踏んだ（`yes` を止めたとき。`SIGKILL: already gone`）。
  **その窓が現実に開いていることの傍証**

`ProcessLookupError` と一般の `OSError` の切り分け（`timer.py:425-430`）
自体は妥当。`start_new_session=True` により pgid == 直の子の pid に
なるので、グループ id の指し方も正しい。

案: `kill_alarm_cmd()` の中でも直前に `proc.poll() is None` を確かめる
（窓は狭くなるが消えない）か、`proc.send_signal()` でシェルを落として
から孫を追う形にする。少なくとも「なぜ `Popen.send_signal()` を使わず
生の `killpg` なのか」をコメントに残したい。

### 2-5. 同じ `Timer` で `main()` を 2 回呼ぶと、コマンドを止められない（実測）

`alarm_proc` / `alarm_proc_ready` / `alarm_cmd_stopped` は
`__init__`（`timer.py:112-115`）でしか初期化されず、`main()` や
`ring_alarm()` では戻らない。2 回目の `main()` では

- `alarm_proc_ready` が立ったままなので待たずに進み、
- `alarm_proc` が**前回の**（終了済みの）proc なので `poll()` が
  非 None → `return True` → 上限なしの `join()`

となる。実測（`--cmd "sleep 4"`、毎回すぐキーを押す）:

| 回 | `main()` の所要 |
|---|---|
| 1 回目 | 0.21 秒 |
| 2 回目 | **4.20 秒** |

ポモドーロはフェーズごとに `Timer` を作り直すので CLI では踏まない。
ただし `CLAUDE.md` は「`Timer` / `PomodoroTimer` をライブラリとして
直接使う経路」を明示的に想定している（TODO-012 の二重検証の理由）ので、
`main()` の冒頭で 3 つを初期化するのが筋だと思う。

### 2-6. テストが `os.killpg` を patch していない経路がある

`tests/test_timer.py` の `mock_subprocess` は `proc.pid = 12345` という
**実在しうる pid** を返す。`test_main_quit_with_alarm_cmd` /
`test_main_with_alarm_cmd_failure` は `mock_killpg` を使っていない。
いまは `poll.return_value = 0`（終了済み）なので `killpg` に到達しないが、
`stop_alarm_cmd()` の早期 return を直す（指摘 2-3）と到達しうる。
そのとき**テストが開発機の無関係なプロセスグループへ `SIGTERM` を撃つ**。

案: `killpg` に到達しうるテストには必ず `mock_killpg` を付ける、
`pid` を `-1` や巨大値ではなく「絶対に存在しない」値にする、
あるいは `conftest.py` で `os.killpg` を全体的に塞ぐ。

### 2-7. `os.killpg` / `signal.SIGKILL` / `start_new_session` は POSIX 専用

`timer.py:424, 461-464, 386-388`。Windows では `os.killpg` も
`signal.SIGKILL` も無いので、**コマンド実行中にキーを押した瞬間に
`AttributeError`** になる（ビープの経路は無事）。`pyproject.toml` に
OS の分類子は無く、`README.md` の Requirement にも記述が無い。
`blessed` には `win_terminal.py` があるので、ライブラリとしては
Windows も一応射程に入っている（tmr が実際に動くかは **未確認**）。

案: 「POSIX 前提」と `docs/Developer.md` か `README.md` に 1 行書く、
または `hasattr(os, "killpg")` で分岐する。方針を決めるだけでもよい。

### 2-8. テストが押さえていない分岐

新しいテストは、SIGTERM → SIGKILL → 諦めの 3 段と、
`ProcessLookupError` / `PermissionError` の別、ビープ経路、
`[Q]` で `True` を返すこと（1 巡目の指摘 6 の要）を押さえていて、
分岐の意味を見る形になっている。抜けているのは:

- **`alarm_proc_ready` の競合**（実装担当が「これが無いと固まる」と
  書いた当の理由）を固定するテストが無い。`Popen` の `side_effect` を
  遅らせて、その間に `stop_alarm_cmd()` を呼ぶ形で書ける
- **自然に終わったコマンドにシグナルを送らないこと**の assert が無い
  （`mock_killpg.assert_not_called()` が欲しい。指摘 2-6 とも絡む）
- 出力（`stdout` / `stderr`）をログに回す分岐（`timer.py:397-399`）の
  テストが無い
- `Ctrl-C`（指摘 2-1）は自動テストが難しいので、直すなら手順を
  `archives/todo/` 側に残す形でよいと思う

---

## 好みの範囲

- `ALARM_STOP_SEC` は 3 か所（ready 待ち・SIGTERM 後・SIGKILL 後）で
  効くので、最悪 3 秒待ってから `main()` が返る。`docs/Developer.md` は
  「`ALARM_STOP_SEC`（1 秒）待つ」としか読めないので、合計の上限を
  書いておくと親切
- `docs/User.md` に、`Ctrl-C` で終わらせたときの挙動（指摘 2-1 を
  直さないなら「コマンドは止まらない」）を 1 行書きたい

---

## 対応が確認できた点（短く）

- **usage error への統一**（1 巡目の指摘 2, 3）: `cli.py:34-43` の
  `_reject_empty` が `_reject_non_finite` と同じ形で、両コマンドに
  付いている（`cli.py:100, 183`）。`AlarmParams` の `ValueError` も
  残っており、`CLAUDE.md` の二重の作りに揃った。設定ファイル経由でも
  終了コード 2 になることが `tests/test_config.py` で固定されている
- **`thr_alarm()` の `params.cmd is not None`**（`timer.py:474`）:
  意図どおりの書き方に変わった
- **`stdin=DEVNULL`**（`timer.py:379`）: 打鍵の取り合いは無くなった。
  `docs/User.md` の「コマンドはキーボードを読めません」も正しい
- **`-d` の説明の訂正**（`docs/User.md`）: 「失敗は `-d` 無しでも警告」と
  直っており、1 巡目の指摘どおり
- **`main()` の戻り値**: cmd 経路の `[Q]` で `True`（`timer.py:286-287` は
  素通し、`test_main_quit_with_alarm_cmd` で固定）。ポモドーロの
  フェーズ制御は壊れていない
- **`alarm_active` の合流**: cmd 経路ではスレッド側が触らず、
  メインループ側だけが `timer.py:280` で False にする。`stop_alarm_cmd()`
  はその後に呼ばれるので、状態の食い違いは無い
- **`docs/Developer.md`**: 「アラームの待ちループは止まらないが、
  キーを押したあとの後始末では待つ」と書き分けられている（1 巡目の
  指摘に対応）。ただし指摘 2-3 の抜け道はこの記述からも読めない

---

# 3 巡目（`main()` / `_main()` 分離と `KeyboardInterrupt` の扱い）

対象: `implementer-report.md` の「3 巡目」の節と現在の `git diff`
（+ 未追跡の `tests/conftest.py`）。2-2 / 2-3 / 2-7 は見送りの決定に
従い、再提起しない。

## 要修正

**無し。**

2-1 / 2-4 / 2-5 / 2-6 / 2-8 の対応は、いずれも狙いどおりになっている
（下の「確認した点」）。以下は程度の軽いものだけ。

---

## 検討

### 3-1. 2 度目の `Ctrl-C` で子プロセスが残る（実測）

`main()`（`timer.py:242-247`）の `except KeyboardInterrupt:` の中で
`stop_alarm_cmd()` を呼ぶが、**その呼び出し自体は保護されていない**。
`stop_alarm_cmd()` は最悪 3 秒（起動待ち 1 + `SIGTERM` 後 1 +
`SIGKILL` 後 1）かかるので、その間に 2 度目の `SIGINT` が来ると
`KeyboardInterrupt` が `except` 節の中から飛び出し、
`TerminalContext` が握り潰して終了する。**`SIGKILL` を送る前に
抜けるので、`SIGTERM` を無視するコマンドは生き残る。**

実測（`pty.fork()` で疑似端末を作り、`TIME UP` 後に `\x03` を送る。
`uv run tmr pomodoro -w 0.02 -b 0.02 -c 2 --cmd "<cmd>"`）:

| cmd | `Ctrl-C` | 残骸（`pgrep`） |
|---|---|---|
| `sleep 311` | 1 回 | 無し |
| `trap '' TERM; sleep 313` | 1 回 | 無し（`SIGKILL` まで進む） |
| `trap '' TERM; sleep 314` | **2 回（0.3 秒間隔）** | **`/bin/sh` と `sleep` が残った** |

「効かないからもう一度押す」は利用者が普通にやる操作なので、
一応挙げておく。ただし条件（`SIGTERM` を無視するコマンド ＋
1 秒以内の 2 度目）は狭く、直さないという判断も理解できる。

案: `except` 節の中を `try: ... except KeyboardInterrupt: pass` で
包む（2 度目は無視して後始末を終わらせる）。テストも
`stop_alarm_cmd` の `side_effect` に `KeyboardInterrupt` を置けば書ける。

### 3-2. `docs/User.md` の `&` の書きぶりが、実際より軽い（実測）

`docs/User.md:270-273`:

> **`&` を付けてバックグラウンドにする書き方**（`aplay foo.wav &` など）。
> キーを押しても、そのプロセスがすぐには止まらないことがあります

実際は「そのプロセスが止まらない」だけでなく、**tmr 自体が
そのコマンドの終了まで返らない**。実測（3 巡目のコードで再確認。
アラームに入って 1 秒後に `[Q]`、`--cmd "sleep 8 &"`）:
`main()` の所要 **8.21 秒**（本来 1.2 秒）。ポモドーロなら次のフェーズも
その間止まる。

`docs/Developer.md` 側は「`communicate()` が返らないまま `join()` で
待ちます」と正しく書けているので、`docs/User.md` も
「**tmr がそのコマンドの終了まで止まって見えます**」まで書かないと、
読んだ利用者が「音が鳴り続けるだけ」と受け取る。見送りの範囲を
広げる話ではなく、注意書きの強さの話。

### 3-3. 後始末が `KeyboardInterrupt` 限定

`timer.py:242` は `except KeyboardInterrupt` だけなので、表示側の
バグなど**他の例外で抜けたときは子が残る**（`stop_alarm_cmd()` を
通らない）。`try/finally` にすれば全経路を覆える。正常経路では
`_main()` の中（`timer.py:314`）で既に止めており、`stop_alarm_cmd()` は
`poll()` を見て「終わっていれば何もしない」ので、二重に呼んでも
実害は無い（＝ `finally` 化は安全）。優先度は低い。

### 3-4. `alarm_thr` の代入がスレッド起動の外にある

`timer.py:284-285`:

```python
if (thr := self.ring_alarm()):
    self.alarm_thr = thr  # KeyboardInterrupt のときの後始末用
```

スレッドは `ring_alarm()` の中で `start()` 済みなので、
**`start()` から代入までの数バイトコードの間に `SIGINT` が来ると
`alarm_thr` が `None` のままで後始末が走らない**。窓は極めて狭く、
**未確認**（実測していない）。`ring_alarm()` の中で
`self.alarm_thr = thr` してから返せば、この窓は消える。

### 3-5. 止めそこねたスレッドが、後から誤った警告を出す

`stop_alarm_cmd()` が False を返した場合（`killpg` が失敗した、
`SIGKILL` 後もスレッドが生きている）、そのスレッドは生きたまま
`main()` が返る。同じ `Timer` で 2 回目を回すと `_main()`
（`timer.py:255`）が `alarm_cmd_stopped = False` に戻すので、
古いスレッドの `exec_alarm_cmd()` が後から
`timer.py:429-433` に到達したとき、**自分で止めたのに
`returncode=-15` を `warning` として出す**（2 回目の表示に混ざる）。
コードから読める範囲の指摘で、**未実測**。踏む条件は狭い
（`stop_alarm_cmd()` が False を返したうえで再実行）ので、
直すなら「初期化するのは `alarm_cmd_stopped` 以外」程度の話。

### 3-6. `conftest.py` の封鎖範囲（広すぎではないが、限定もされていない）

`tests/conftest.py` の `patch("tmr.timer.os.killpg")` は、
`tmr.timer.os` が `os` モジュール**そのもの**なので、実体は
`patch("os.killpg")`。docstring は `tmr.timer` に限った話に読めるが、
テストの間はプロセス全体で効く。今のテストは他に `killpg` を使わない
ので実害は無い。

**確かめたいものを潰してはいない**: `tests/test_timer.py` の
`mock_killpg` は同じ対象を内側で patch し直すので、
`assert_called_once_with(...)` も `assert_not_called()` も
内側のモックを見ており、有効。

覚えておきたいのは、この安全弁が塞ぐのは `killpg` **だけ**という点。
実装が `proc.terminate()` / `os.kill()` に変わると、黙って効かなくなる。

---

## 好みの範囲

- `docs/Developer.md` の「`main()` の冒頭で … 初期化します」は、
  実際には `_main()` の冒頭（`timer.py:253-257`）。読み替えられる範囲
- `Ctrl-C` の後始末で最悪 3 秒無反応になりうることは
  `docs/Developer.md` にはあるが、`docs/User.md` には無い

---

## 確認した点（重点項目への回答）

1. **`KeyboardInterrupt` を捕まえて再送出する形**: 正しい。
   `raise` で送出し直すので `TerminalContext` の握り潰し
   （`terminal.py:26-29`）と二重にはならず、`Aborted.` は 1 回だけ出る
   （pty で実測）。`main()` の戻り値による制御は例外経路では使われず、
   `PomodoroTimer.run()`（`pomodoro.py:88-97`）は例外を素通しするので
   `cli.py` の `TerminalContext` まで届く。実測（`-c 2` で 1 フェーズ目に
   `Ctrl-C`）: 2 フェーズ目に進まず終了、残骸なし。**ポモドーロは
   `Ctrl-C` で正しく止まる**。2 度目の `Ctrl-C` だけが 3-1
2. **`_main()` への分離と端末の後始末**: 範囲はずれていない。
   `with self.term.cbreak()` は `_main()` の中に閉じているので、例外は
   まず blessed の `__exit__` で termios を戻してから `main()` の
   `except` に届く。カーソルは呼び出し側の `TerminalContext` が戻す。
   端末が壊れた状態で残る経路は見当たらない（`stop_alarm_cmd()` は
   端末に触らない）
3. **初期化と生きているスレッドの競合**: 古いスレッドは `Popen` の
   直後にしか `alarm_proc` / `alarm_proc_ready` を書かないので、
   2 回目の `_main()` の初期化と取り合いにならない。影響は 3-5 の
   ログ水準だけ
4. **`conftest.py`**: 3-6 のとおり、確かめたい呼び出しは見えている
5. **追加された 7 件**: 分岐の意味を押さえている。特に
   `test_main_keyboard_interrupt_stops_alarm_cmd` は
   **アラームの待ちループの中から** `KeyboardInterrupt` を飛ばす形
   （`get_key_name` の `side_effect`）で、実際の経路と同じ。
   `test_stop_alarm_cmd_waits_for_popen`（起動前の競合）、
   `test_main_resets_alarm_cmd_state`（2 回目）、
   `mock_killpg.assert_not_called()`（自然終了・起動失敗には撃たない）、
   出力の切り詰めも押さえている。抜けているのは 3-1 の経路だけ
6. **2-4 の poll() 追加**（`timer.py:455-458`）と、なぜ
   `Popen.send_signal()` を使わないかの docstring は妥当。
   窓が完全には消えないことも実装担当が報告に書いている
7. **文書**: `yes` / `tail -f` の注意（`docs/User.md:266-269`）は実態と
   合っている（2 巡目に `yes` で OOM kill を実測済み）。
   `Ctrl-C` でもコマンドが止まる旨（`docs/User.md:250-252`）も、
   1 回押しなら実測どおり。`&` の書きぶりだけが 3-2
8. **テスト実行**: `uv run pytest tests -q` → **188 passed**（1.33 秒）。
   `tests/conftest.py` の autouse fixture を入れても
   `tests/test_integration_alarm.py`（ビープの実スレッド）は影響を
   受けていない（`killpg` を使わないため）

---

# 4 巡目（`SIGINT` のマスクと `SIG_SETMASK` への変更）

対象: `implementer-report.md` の「4 巡目」の節と現在の差分
（`timer.py` の `cleanup_by_interrupt()` / `ring_alarm()`、
`tests/test_timer.py` のマスク関連 3 件、`docs/*`）。
2-2 / 2-3 / 2-7 と 3 巡目の「検討」4 件は再提起しない。

## 要修正

**無し。**

3-1（2 度目の `Ctrl-C`）は直っていることを自分でも実測した。
`SIG_UNBLOCK` → `SIG_SETMASK`（管理者の修正）も**正しく、かつ
実際に違いが出る**ことを実測で確かめた（下記）。ビープ経路の回帰も
見当たらない。

---

## 検討

### 4-1. アラームのコマンドが `SIGINT` を止めた状態で起動される（実測。副作用）

`ring_alarm()`（`timer.py:575-579`）で `SIGINT` を止めてから
`thr.start()` するので、アラームのスレッドは `SIGINT` を止めた状態で
動く。`Popen` はそのスレッドから呼ぶので、**子プロセスがその
シグナルマスクを継ぐ**（`exec` はマスクを引き継ぐ。`subprocess` の
`restore_signals=True` が戻すのは `SIG_IGN` の**ハンドラ**だけで、
マスクは戻さない）。

実測（`--cmd "grep SigBlk /proc/self/status"` 相当を、実際の
`Timer.ring_alarm()` 経由で動かしてログの `stdout:` を読んだ）:

| 起動元 | 子の `SigBlk` |
|---|---|
| アラームのスレッド（現在の実装） | `0000000000000002` = **`SIGINT` が止まっている** |
| メインスレッド（3 巡目までと同じ状態） | `0000000000000000` |

tmr 自身の停止手順は `SIGTERM` / `SIGKILL` なので影響を受けない
（TERM を無視するコマンドが `SIGKILL` で止まることは実測済み）。
問題になるとすれば、指定したコマンドの中で `SIGINT` を使う場合
（スクリプトが子に `kill -INT` する、対話的なプログラムを起動する等）で、
**利用者から見えない形で実行環境が変わっている**点。

直すなら `Popen` の直前だけマスクを戻す形になるが、その窓で
アラームのスレッドが `SIGINT` を受け取りうる（4 巡目で潰した当の問題）
ので、トレードオフになる。**「このまま許容して `docs/Developer.md` に
1 行残す」で十分**だと思う。判断をお願いしたい。

### 4-2. マスクを取得してから `try:` に入るまでの窓

`cleanup_by_interrupt()`（`timer.py:266-268`）と
`ring_alarm()`（`timer.py:575-577`）は、どちらも

```python
old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
try:
    ...
finally:
    _ = signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
```

の形。`SIG_BLOCK` が返ってから `try:` に入るまでの 1〜2 バイトコードの
間に、**ブロックする前に届いていた `SIGINT`** が
`KeyboardInterrupt` として上がると、`finally` を通らずに抜けるので
**`SIGINT` を止めたまま**になる。

- CLI ではそのまま `TerminalContext` → プロセス終了なので実害は無い
- `Timer` をライブラリとして使い、`KeyboardInterrupt` を捕まえて
  動き続ける側では、**`Ctrl-C` が効かない状態が残る**
- 窓は極めて狭く、**未確認**（再現はしていない）

`old_mask = None` を先に置いて `try:` の中で `SIG_BLOCK` し、
`finally` で `if old_mask is not None:` とすれば閉じられる。

### 4-3. マスクのテストが「順序」を固定していない

`test_ring_alarm_blocks_sigint_for_thread`（`tests/test_timer.py:700`）と
`test_cleanup_by_interrupt_restores_sigmask`（同 725）は、
`pthread_sigmask` の呼び出しが
`[(SIG_BLOCK, {SIGINT}), (SIG_SETMASK, 元のマスク)]` の 2 回であることを
見ている。**元のマスクへ戻すこと**（管理者の修正点）は確かに固定できて
いて、ここは良い。

ただし**その間に `thr.start()` / `stop_alarm_cmd()` が起きたこと**は
見ていないので、`thr.start()` をマスクの外に出す変更をしても
両方とも通る。肝心の「スレッドが起動する時点で止まっていること」が
テストからは落ちている。

- `mock.attach_mock()` で `Thread.start` と `pthread_sigmask` を
  1 つの親モックにまとめれば、`parent.mock_calls` で順序を固定できる
- あるいは、**実際のマスクを見るテスト**（`thr_alarm` を差し替えて
  スレッドの中で `signal.pthread_sigmask(SIG_BLOCK, [])` を記録し、
  `SIGINT` が入っていることを assert する）を 1 件足せば、
  仕組みそのものを固定できる。私はこの形で手元で確かめた
  （下記の実測）ので、テストにもできるはず

---

## 好みの範囲

- `docs/Developer.md:289-296` はマスクのことを書いているが、
  **「解除ではなく元のマスクへ戻す」理由**（呼ぶ側が `SIGINT` を
  止めていることがある）は、コードのコメントとテストの docstring に
  しか無い。1 行あってもよい
- 後始末の間に止めているのは `SIGINT` だけなので、`Ctrl-\`（`SIGQUIT`）で
  抜けられると子が残る。実際に押す人はまずいないので、直す必要は
  無いと思う

---

## 実測（重点項目への回答）

`pty.fork()` で疑似端末を作り（`TIOCSWINSZ` で 100x24）、
`uv run tmr pomodoro -w 0.02 -b 0.02 -c 2` に外から入力を送った。
残骸の確認は `pgrep` → PID 指定の `kill`（`pkill` は不使用）。

| # | 経路 | 送ったもの | 結果 |
|---|---|---|---|
| A | **ビープ**（`--cmd` なし） | アラーム中に `Ctrl-C` | 0.06 秒で終了、`Aborted.` |
| B | ビープ | カウントダウン中に `Ctrl-C` | 0.06 秒で終了、`Aborted.` |
| C | cmd（`trap '' TERM; sleep`） | `Ctrl-C` 2 回（0.3 秒間隔） | **1.05 秒で終了、残骸なし**（`SIGKILL` まで進んだ） |
| D | ビープ | `Ctrl-C` 2 回 | 0.06 秒で終了 |
| E | ビープ | `[N]` で 2 フェーズ目へ → `Ctrl-C` | **0.05 秒で終了**（マスクは残っていない） |
| F | cmd（`sleep`） | `[N]` で 2 フェーズ目へ → `Ctrl-C` | **0.09 秒で終了、残骸なし** |

3. **ビープ経路の回帰は無い**（A / B / D / E）。`--alarm-count 0` は
   スレッドの中身が違うだけで `ring_alarm()` の作りは同じなので、
   同じ扱いになる（テスト `test_ring_alarm_blocks_sigint_for_thread` が
   `AlarmParams(0, 0.0, 0.0)` を使っている）。

1・2. **マスクの復元**は、実際のマスクを読んで確かめた
（`Terminal` / `TimerView` をモックし、`thr_alarm` を差し替えて
スレッド内のマスクを記録）:

| 見た場所 | `SIGINT` |
|---|---|
| `ring_alarm()` の前後（メインスレッド） | 通る（変化なし） |
| アラームのスレッドの中 | **止まっている**（狙いどおり） |
| `cleanup_by_interrupt()` の後（メインスレッド） | 通る |
| 呼ぶ側が `SIGINT` を止めていた場合の `cleanup_by_interrupt()` の後 | **止まったまま（保たれた）** |
| 同じく `ring_alarm()` の後 | **止まったまま（保たれた）** |

最後の 2 行が管理者の修正点そのもの。`SIG_UNBLOCK` のままなら
ここで**呼ぶ側のマスクを勝手に解除**していたので、
`SIG_SETMASK` + 保存した `old_mask` への変更は正しい。
`finally` に入っているので、`stop_alarm_cmd()` が
`KeyboardInterrupt` 以外の例外を投げた経路でも戻る（コードで確認）。
`cleanup_by_interrupt()` は `main()` の `except` からしか呼ばれず、
`ring_alarm()` のマスクとは同じスレッドで時間的に重ならないので、
入れ子にはならない。仮に入れ子になっても、保存したマスクへ戻す形なら
壊れない。

4. **テスト**: `uv run pytest tests -q` → **191 passed**（2.33 秒）。
   マスク関連 3 件の中身は 4-3 のとおり（元のマスクへ戻すことは
   固定できている。順序は固定できていない）。

5. **副作用**: 4-1（子がマスクを継ぐ）が見つかった。それ以外に、
   マスクを触ったことによる影響は見当たらない
   （`SIGTERM` / `SIGKILL` は止めていないので停止手順は無事。
   `loguru` や `blessed` は別スレッドを作らないので、
   マスクを継ぐスレッドは他に無い）。

## 文書

`docs/User.md:272-277` の `&` の注意は、実測（`--cmd "sleep 8 &"` で
`[Q]` を押しても `main()` が 8.21 秒返らない）と合う書きぶりになった。
3-2 は解消。
