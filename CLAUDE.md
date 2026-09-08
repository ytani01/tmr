# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

`tmr` — ターミナル上で動く CLI タイマー（単純タイマー + ポモドーロ）。

## コマンド

```bash
uv run pytest tests                        # テストだけ流す（最速）
uv run tmr timer 1                         # 手元で動かす（1 分）
uv run tmr pomodoro -w 0.1 -b 0.1 -c 2     # ポモドーロを短時間で確認
```

`mise` のタスクは `build` → `test` → `lint` → `upgradeproject` と
`depends` で数珠つなぎになっている。**`mise run test` / `mise run lint` を
呼ぶと `upgradeproject` が動き、`uv.lock` を削除して `uv sync` し直す。**
普段の確認には上の `uv run ...` を使い、`mise run` はリリース前など
意図があるときだけにする。

lint の中身（`mise run lint` 相当。個別に流すならこの順）:

```bash
uv run ruff format --line-length 78 src tests
uv run ruff check --fix --extend-select I src tests
uv run basedpyright src tests
uv run mypy src tests
```

**行長は 78 文字**（`pyproject.toml` ではなく `mise.toml` の引数で指定）。

## 設計

### Timer は 3 つに分かれている

- `clock.py` の `TimerClock` — 経過時間。端末に触らないので単体で試せる
- `view.py` の `TimerView` — 列の定義、幅に応じた省略、スタイル付け
- `timer.py` の `Timer` — メインループとキー操作・アラーム。
  `Terminal` を作り、`TimerClock` と `TimerView` を持つ

`PomodoroTimer` は `Timer` を**継承せず、順番に呼び出すだけ**の薄い層。

- 時刻は `time.monotonic()`。NTP でシステム時刻が動いても狂わない
- **早送り・巻き戻し・ポーズは `TimerClock.t_start` をずらして表現する**
  （`elapsed` を直接いじらない）。ポーズ中は `t_start = t_cur - elapsed`
  を毎周回し直すことで経過時間を止める
- メインループは `term.cbreak()` の中で `inkey(timeout=0.2)` を回す。
  0.2 秒がそのまま画面の更新間隔になる
- タイトルは `TimerTitle(text, color, width)`、アラームの鳴らし方は
  `AlarmParams(count, sec1, sec2)`。`width` が正なら表示時に桁を揃える
  （ポモドーロがフェーズ名を 16 桁で並べるのに使う）
- 0 以下・`nan`・`inf` の時間やサイクル数は、CLI では `click.IntRange` /
  `click.FloatRange` とコールバックで弾き、`TimerClock` /
  `PomodoroConfig` / `AlarmParams` でも `ValueError` で弾く二重の作り。
  `Timer` / `PomodoroTimer` をライブラリとして直接使う経路は CLI を
  通らないため（TODO-012）。**ただしアラームの回数と間隔は 0 を許す**
  （鳴らさない／間を空けない）。間隔は `time.sleep()` が
  `OverflowError` にならないよう 1 日（`timefmt.SEC_DAY`）を上限とする

### 戻り値でフェーズを制御する

`Timer.main()` は **quit コマンドで終わったときだけ `True`** を返す。
`PomodoroTimer.run()` はこれを見てサイクル全体を打ち切る。
`next`（`enable_next=True` のときだけ有効）はタイマーを終わらせるが
`True` を返さないので、次のフェーズへ進む。この 2 つの区別が
ポモドーロの唯一の制御経路。

### 表示は col_list() 1 つで決まる

`TimerView.col_list()` が返すリストの**並び順が画面上の並び順**で、
各 `TimerCol` の **`priority` が幅の足りないときに削る順**
（小さいものから削られる）。表示項目を足すときは、`col_list()` に
1 行足し、`display()` でその列に値を入れる（`title` のように
`__init__` で入れるものは除く）。

`TimerView.display()` は端末幅に収まるまで `priority` の低い項目を
落とし、最後に残った幅を `pbar` に割り当てる。

`rate_color=True` の列は経過率に応じて `PERCENT_COLOR` の色に変わり、
`pause_blink=True` の列はポーズ中に点滅する。

秒数を `"1h01m01s"` のような文字列にする `t_str()` と、時間の単位
（`SEC_MIN` / `MIN_HOUR`）は `timefmt.py` にある。

### キー割り当て

`cmd_list()` が返す `TimerCmd` から `key_map = {key: fn}` を組み立てる。
キーを増やすときは `cmd_list()` の該当エントリに足すだけでよく、
ヘルプ（`fn_help`）の表示も自動で追随する。キー名は blessed の
`inkey().name`（`KEY_LEFT` など）か、大文字化した 1 文字。
表示用の整形は `KEY_WORD_MAP` + `keys_str()`。

### アラームと端末の後始末

- アラームは daemon スレッドで `\a` を鳴らす。停止の合図は
  `alarm_active` フラグ 1 つ（スレッド側もメインループ側も見ている）
- `TerminalContext`（`terminal.py`）が**カーソルの復帰と
  `KeyboardInterrupt` の握り潰し**を担当する。端末を触る処理は
  必ずこの `with` の中に置く。CLI 側では `cli.py` の各コマンドが
  これで包んでいる

### ログ

`loguru` のグローバル logger を、`mylog.getLogger()` で名前を付けて使う。
クラスのあるモジュールでは、クラス本体に
`__log = getLogger(__qualname__)`（アンダースコア 2 つ）を 1 つ置き、
そのクラスのメソッドでは `self.__log.debug(...)` のように呼ぶ
（`timer.py` / `progress_bar.py` 参照）。`__qualname__` はクラス
本体の実行前に暗黙で入る変数で、クラス名がそのまま入る（クラス名を
手で書かずに済み、変えたときのずれも無くなる）。名前修飾で
`self._Timer__log` に解決されるので、子クラスのインスタンスから
親のメソッドを呼んでも親の名前で出る。`_log`（1 つ）だと MRO で
子クラスの定義が勝ち、親のログが子の水準で出てしまうので使わない。
クラスの無いモジュール（`cli.py`）は、モジュール先頭に
`_log = getLogger("main")` を置く。

`__init__` の中で `self.__log = ...` はしない。クラス本体に置くことで、
`super().__init__()` を呼び忘れても親のログが `AttributeError` に
ならず、`classmethod` からも使え、インスタンスを作る前から水準が効く。

水準は、普段はクラス本体の `getLogger(name, level)` で指定する。
テストや実行中など外から変えるときだけ `setLevel(name, level)` を使う
（`getLogger()` の `level` 引数は内部で `setLevel()` を呼ぶだけ）。
知らない水準名を渡すと `ValueError` になる。`setLevel()` で変えた水準を
既定に戻すには `setLevel(name, None)`（`level` 省略）を使う
（TODO-005）。

各 CLI コマンドの先頭で `loggerInit(debug)` を 1 度だけ呼ぶ規約
（`Timer` をライブラリとして使う側も同じ）。`debug` は名前を
指定していないログの既定水準（`DEBUG` / `INFO`）を決める。
`getLogger()` / `setLevel()` で指定した名前ごとの水準は、
呼ぶ順に関わらず `loggerInit()` で上書きされない
（実行時に環境変数で切り替える用途が無いため、TODO-003 で
`TMR_LOG` は廃止した）。

### 設定ファイル

`config.py` が `~/.config/tmr/config.toml`（`XDG_CONFIG_HOME` があれば
その下）を読み、`click` の `default_map` を作る。優先順位
**コマンドライン引数 > 設定ファイル > コードの既定値** は `click` 側が
面倒を見るので、各コマンドの定義には手を入れていない（TODO-001）。

`cli` は `ConfigGroup`（`click.Group` の子）で、`make_context()` の中で
設定を読む。**サブコマンドを直接 `invoke()` しても設定は読まれない**
（`tests/test_timer.py` などが影響を受けないのはこのため）。設定を
絡めたテストは `cli` から呼び、`XDG_CONFIG_HOME` を `tmp_path` に
向けること（`tests/test_config.py` 参照）。

セクション名は**サブコマンドの正式名**（別名 `t` / `p` は書けない）。
`default_map` は別名にも同じ dict を張るので、`tmr t` でも `[timer]` が
効く。キーはオプション名から `--` を取ったもので、`-` と `_` の
どちらでも書ける。`timer` の `minutes` は引数だが、これも対象
（`default_map` があれば省略できる）。

ファイルが無ければ黙って既定値。**壊れていれば `ClickException` で
終了する**（TOML の構文エラー、知らないセクション、知らないキー）。
値の型が合わない場合は `click` が弾く。

`config.py` は `loggerInit()` より前に動くので**ログを出さない**
（`loguru` の既定ハンドラに素通しされ、毎回出てしまう）。読んだ結果は
`cli` の中で `ctx.default_map` として出す。

### バージョン

`hatch-vcs` で git タグから決まる。`__init__.py` は
`importlib.metadata.version()` で読み、未インストールなら `"0.0.0"`。
ソースに版番号を書かない。

## テスト

`unittest.mock.patch` で差し替えるのが基本形。**モジュールごとに
patch 先が違う**ので注意する。

| テスト | patch する先 |
|---|---|
| `tests/test_timer.py` | `tmr.timer` の `Terminal` / `TimerView` / `click` / `time`（アラームの sleep）、`tmr.clock` の `time`（経過時間） |
| `tests/test_view.py` | `tmr.view` の `ProgressBar` / `click`。`Terminal` は `MagicMock` を渡す |
| `tests/test_clock.py` | `tmr.clock` の `time` だけ（端末に依存しない） |

CLI は `click.testing.CliRunner` + `Timer` のモック
（`tests/test_cli.py`）。スレッドが絡む部分だけ実物を動かす統合テストが
`tests/test_integration_alarm.py` にある。

`Terminal` をモックするときは `term.width` に**数値**を入れること
（`TimerView.display()` が幅と比較するため、MagicMock のままだと落ちる）。

## 補足

- `archives/` 直下の `20260211-*.md` などは、この運用を始める前の
  コードレビュー結果で、**現行の仕様ではない**。実装の根拠として
  参照しない（`archives/todo/` とは別物）
- オプションを変えたら `README.md` の help 出力も直す
