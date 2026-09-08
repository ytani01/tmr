# TODO-017 verifier 報告

## 対象

`git status` の時点で未コミットの変更は `CLAUDE.md` / `README.md` /
`docs/Developer.md` のみ。`docs/User.md` は変更されていなかったので、
実装との照合だけ行った（一致していたので変更が不要という判断のよう
だが、その判断の妥当性はこの報告で検証した内容から支持できる）。

## 検証（すべて一致。不一致なし）

### 1. help 出力の再現

```
uv run tmr --help
uv run tmr timer --help
uv run tmr pomodoro --help
```
の実際の出力を、`docs/User.md` の該当ブロック（7-27, 36-52, 71-86 行目）
と突き合わせ、**1 文字単位で一致**を確認した（オプション名、既定値、
`RANGE` の範囲表示すべて含む）。`README.md` には help 出力ブロックは
無く、突き合わせ対象は無かった。

### 2. `COMMAND LIST`（キー操作の一覧）

`docs/User.md` 114-125 行目の一覧を、実装（`Timer.cmd_list()` /
`mk_cmd_str()` / `keys_str()`）を直接呼ぶスクリプトで再現し、
**1 行単位で一致**を確認した（`enable_next=True` のとき）。

`enable_next=False`（`tmr timer` 相当）でも同じスクリプトを流し、
`next`（`[N], [ENTER]`）の行が一覧から消えることを確認した。これは
docs/User.md 127-128 行目「`[N]` / `[ENTER]`（Next）はポモドーロでだけ
有効です。`tmr timer` では一覧にも出ません」と一致する。

### 3. 端末幅による表示の省略（docs/User.md 174-196 行目）

`TimerView` に `term.width` を 70/50/40/30/25/15/10 に変えたモックを
渡すスクリプトで、docs の例と同じ `elapsed=10m30s` / `remain=14m30s` /
`limit=25m`（rate=42.0%）を再現した。7 段階すべてで
**表示文字列が完全一致**した。

落ちる順の表（191-193 行目: `date, time, elapsed, rate, limit, pbar,
state, title, remain`）も、`view.py` の `col_list()` の priority
（date=1, time=2, elapsed=3, rate=4, limit=5, pbar=6, state=7, title=8,
remain=9）を昇順に並べた順と一致した。

色の閾値（169 行目「80% 以上で黄、95% 以上で赤」）は
`TimerView.PERCENT_COLOR = {"white": 0, "yellow": 80, "red": 95}` と一致。

### 4. `--cmd ""` のエラー

```
$ uv run tmr timer 5 --cmd ""
Usage: tmr timer [OPTIONS] MINUTES
Error: Invalid value for '--alarm-cmd' / '--cmd': must not be empty: ''
$ echo $?
2
```
空白のみ（`"   "`）でも同じ。docs/User.md 264 行目の記述と一致。

### 5. bash ブロックの動作確認

- `tmr timer 5` / `tmr pomodoro`（stdin に `q` を流し `timeout 5` で
  実行）: どちらも例外なく起動し、想定どおりの列（date/time/title/
  limit/rate/elapsed/pbar/remain）が表示された
- `uv run ruff format --line-length 78 --check src tests` →
  `25 files already formatted`（終了コード 0）
- `uv run ruff check --extend-select I src tests` →
  `All checks passed!`（終了コード 0）
- `uv run basedpyright src tests` → `0 errors, 0 warnings, 0 notes`
- `uv run mypy src tests` → `Success: no issues found in 25 source files`
- `uv run pytest tests -q` → `191 passed`
- `mise run build` などの `mise` タスクは、`uv.lock` を消すため
  **実行していない**（CLAUDE.md 自身の指示どおり）。代わりに
  `mise.toml` を読み、`build → test → lint → upgradeproject` の
  `depends` の連なりと、`upgradeproject` が `rm -f uv.lock; uv sync`
  することを確認した

### 6. 記述と実装の照合

- `docs/Developer.md` のモジュール構成表: `src/tmr/*.py` の実ファイルと
  役割の記述が一致（`__init__.py` / `__main__.py` は表に無いが、
  アーキテクチャ上の主要モジュールではないので妥当と判断）
- 表示列の priority 表（154-164 行目）: `view.py` の `col_list()` と
  一致（上記 3. で実測済み）
- テストの patch 先の表（`tests/test_timer.py` の
  `Terminal`/`TimerView`/`click`/`time`/`subprocess`、`tests/test_view.py`
  の `ProgressBar`/`click`、`tests/test_clock.py` の `time`）:
  各テストファイルの `patch("tmr...")` 呼び出しを `grep` し、一致を確認
- アラームまわりの手順（`exec_alarm_cmd` / `stop_alarm_cmd` /
  `cleanup_by_interrupt` / `ring_alarm`、`cli.py` の `_reject_empty`）:
  すべて実装に存在することを `grep` で確認。`tests/conftest.py` の
  `block_killpg`（autouse で `tmr.timer.os.killpg` を patch）、
  `tests/test_timer.py` の `mock_killpg` fixture も実在を確認
- `pomodoro.py` の `PomodoroConfig` / `phases()` / `TITLE_WIDTH = 16`:
  実装を読み、README.md の mermaid 図（WORK:1/4→SHORT_BREAK:1/4→…→
  LONG_BREAK:4/4→繰り返す）が `phases()` のループ構造と一致することを
  確認
- CLAUDE.md の「行長は 78 文字（`pyproject.toml` ではなく `mise.toml`
  の引数で指定）」: `pyproject.toml` に `line-length` の指定なし、
  `mise.toml` の `lint` タスクにのみ `--line-length 78` があることを
  確認

### 7. リンク切れ

`README.md` / `docs/User.md` / `docs/Developer.md` / `CLAUDE.md` 内の
すべての相対リンク（`docs/fig1.png`、`docs/User.md`、`docs/Developer.md`、
`../README.md`、`User.md`）が実在するファイルを指していることを確認した。
切れているリンクは無かった。

## 確かめられなかったもの

- 実端末（TTY）でのキー入力・アラーム鳴動・点滅表示そのものは、この
  環境がパイプ経由の非対話実行のため、目視での確認はできなかった。
  代わりに `Timer` の内部関数を直接呼ぶスクリプトで表示文字列を再現し、
  文字単位で突き合わせた（上記 2, 3）。これで「書いたとおりに動くか」は
  確かめられたと考えるが、実際の色付け・点滅・ベル音の見た目までは
  未確認
- `docs/User.md`「アラーム」節の、コマンドが長く鳴る場合に `[Q]`/`[N]`
  ですぐ止まる、`&` を付けた書き方だと止まらない、といった記述は
  `docs/Developer.md`「アラームのコマンド」の記述との整合は確認したが、
  実際に `mpv` 等の長時間コマンドを起動してキー入力で止める再現は
  行っていない（TODO-016 の統合テスト `tests/test_integration_alarm.py`
  と `implementer-report.md` に既存の実機確認記録があるため、今回は
  文書と実装コードの記述レベルの突き合わせに留めた）
- `~/.config/tmr/config.toml` を使った設定ファイルの実地確認は
  `tests/test_config.py` の内容を読んでの確認に留め、実際にファイルを
  置いての手動実行はしていない（docs の記述はテストコードの内容と
  一致）

## 判断が要る点

- 見つかった不一致は無かった。管理者の判断が必要な事項も特に無い

## 追加検証: 設定ファイル

コーディネータからの追加依頼を受け、`XDG_CONFIG_HOME` を一時ディレクトリ
（`/tmp/claude-649/.../scratchpad/xdgcfg` 等）に向けて実際に
`tmr/config.toml` を置き、実行して確かめた。**実際の
`~/.config/tmr/` は触っていない。**

### 1. `docs/User.md` の TOML 例そのままで `tmr timer`（MINUTES 省略）

`docs/User.md` 290-303 行目の例をそのまま `$XDG_CONFIG_HOME/tmr/config.toml`
に置いて `tmr timer`（`MINUTES` 省略）を実行した。

```
2026-09-08 21:17:58 Work  5m   0.1%  0m00s |___...  4m60s
```

`minutes = 5` が効いて `5m` で起動し、タイトルも `title = "Work"` が
反映された。

### 2. `tmr t`（別名）でも `[timer]` が効くか

同じ設定ファイルのまま `tmr t` を実行した。

```
2026-09-08 21:18:03 Work  5m   0.1%  0m00s |___...  4m60s
```

`tmr timer` と同じ結果になり、`[timer]` セクションが別名 `t` でも
効くことを確認した。

### 3. `title_color` のようにアンダースコアで書いても効くか

```toml
[timer]
minutes = 7
title_color = "magenta"
```

`tmr -d timer` の debug ログで `default_map` を確認:

```
default_map={'timer': {'minutes': 7, 'title_color': 'magenta'}, 't': {'minutes': 7, 'title_color': 'magenta'}}
```

さらに `tmr.cli.Timer` を `unittest.mock` で差し替えて `CliRunner` から
`tmr timer` を呼び、実際に渡された引数を確認した:

```
call_args: call(TimerTitle(text='Timer', color='magenta', width=0), 420, AlarmParams(...))
```

`title_color`（アンダースコア）が `color='magenta'` として実際に
`Timer` に渡ることを確認した（`420` 秒 = `minutes=7` も反映）。

### 4. コマンドライン引数が設定ファイルより優先されるか

設定に `minutes = 5` がある状態で、同じ `CliRunner` の仕組みを使い
`tmr timer 3` を呼んだ。

```
call_args: call(TimerTitle(text='Work', color='green', width=0), 180, AlarmParams(...))
```

`180` 秒 = 3 分になり、コマンドライン引数が設定ファイルの
`minutes = 5` より優先されることを確認した（`title` / `title_color` は
引数で指定していないので設定ファイルの値のまま）。

### 5. 設定ファイルが無いときは何も言わずに既定値を使うか

`$XDG_CONFIG_HOME/tmr/` を空にした状態（`config.toml` を置かない）で
`tmr timer 1` を実行した。標準エラー出力は空で、コード上の既定値
（`Timer` というタイトル、`1m`）で普通に起動した。

```
--- stderr ---
（空）
--- stdout head ---
2026-09-08 21:19:22 Timer  1m   0.3%  0m00s |___...  0m60s
```

（`timeout` で打ち切ったため終了コードは 124 だが、これは検証手順の
`timeout` によるもので、tmr 自体のエラーではない。）

### 6. TOML の構文エラー / 知らないセクション / 知らないキー

いずれも `ClickException` として `Error: ...` を出し、**終了コード 1**
で終了することを確認した。

```
$ (壊れた TOML: `[timer` で閉じ括弧が無い)
Error: .../config.toml: Expected ']' at the end of a table declaration (at line 1, column 7)
EXIT:1

$ (知らないセクション [unknown_section])
Error: .../config.toml: 知らないセクション: [unknown_section]
EXIT:1

$ (知らないキー [timer] unknown_key)
Error: .../config.toml: [timer]: 知らないキー: 'unknown_key'
EXIT:1
```

docs/User.md 312-314 行目は「エラーを出して終了します」としか書いて
おらず終了コードには触れていないが、実装では 1 で統一されていた
（`click.ClickException` の既定の終了コード）。矛盾ではないが、
終了コードを明記していない点は参考として書き添える。

### 7. 型が合わない値（`minutes = "abc"`）

```toml
[timer]
minutes = "abc"
```

```
$ tmr timer   (MINUTES 省略、config から取る)
Usage: tmr timer [OPTIONS] MINUTES

Error: Invalid value for 'MINUTES': 'abc' is not a valid integer range.
EXIT:2
```

docs/User.md 314 行目「値の型が合わない場合は click が弾きます」の
とおり、`click` 自身のオプション検証（`UsageError`、終了コード 2）で
弾かれることを確認した。ClickException（設定ファイル読み込み時のエラー、
終了コード 1）とは別の経路であることも合わせて確認できた。

### まとめ

`docs/User.md`「設定ファイル」節の 7 項目すべてが、実際にファイルを
置いた実行で記述どおりに動くことを確認した。不一致は無かった。
