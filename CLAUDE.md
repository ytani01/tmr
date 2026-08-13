# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

`tmr` — ターミナル上で動く CLI タイマー（単純タイマー + ポモドーロ）。
Python 3.13+ / src レイアウト / `uv` + `mise`。
依存は `click`（CLI）、`blessed`（キー入力・端末幅）、`loguru`（ログ）。

## コマンド

```bash
uv run pytest tests                        # テストだけ流す（最速）
uv run pytest tests/test_base_timer.py     # ファイル単位
uv run pytest tests/test_base_timer.py::test_fn_pause   # 1 件だけ
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

### BaseTimer が本体

`src/tmr/base_timer.py` にタイマーの仕組みがすべて入っている（534 行）。
`PomodoroTimer` は `BaseTimer` を**継承せず、順番に呼び出すだけ**の薄い層。

- 時刻は `time.monotonic()`。NTP でシステム時刻が動いても狂わない
- **早送り・巻き戻し・ポーズは `t_start` をずらして表現する**
  （`t_elapsed` を直接いじらない）。ポーズ中は `t_start = t_cur - t_elapsed`
  を毎周回し直すことで経過時間を止める
- メインループは `term.cbreak()` の中で `inkey(timeout=0.2)` を回す。
  0.2 秒がそのまま画面の更新間隔になる

### 戻り値でフェーズを制御する

`BaseTimer.main()` は **quit コマンドで終わったときだけ `True`** を返す。
`PomodoroTimer.run()` はこれを見てサイクル全体を打ち切る。
`next`（`enable_next=True` のときだけ有効）はタイマーを終わらせるが
`True` を返さないので、次のフェーズへ進む。この 2 つの区別が
ポモドーロの唯一の制御経路。

### 表示は 2 つのリストで決まる

- `col_list()` が返す dict の**並び順が画面上の並び順**
- `COL_PRIORITY` が**幅が足りないときに削る順**（末尾から `pop`）

`display()` は端末幅に収まるまで `COL_PRIORITY` の末尾から項目を落とし、
最後に残った幅を `pbar` に割り当てる。**表示項目を足すときは両方に足す**
（片方だけだと並び順が崩れるか、幅が足りないときに落とせない）。

`rate_color=True` の列は経過率に応じて `PERCENT_COLOR` の色に変わり、
`pause_blink=True` の列はポーズ中に点滅する。

### キー割り当て

`cmd_list()` が返す `TimerCmd` から `key_map = {key: fn}` を組み立てる。
キーを増やすときは `cmd_list()` の該当エントリに足すだけでよく、
ヘルプ（`fn_help`）の表示も自動で追随する。キー名は blessed の
`inkey().name`（`KEY_LEFT` など）か、大文字化した 1 文字。
表示用の整形は `KEY_WORD_MAP` + `keys_str()`。

### アラームと端末の後始末

- アラームは daemon スレッドで `\a` を鳴らす。停止の合図は
  `alarm_active` フラグ 1 つ（スレッド側もメインループ側も見ている）
- `TerminalContext`（`utils.py`）が**カーソルの復帰と
  `KeyboardInterrupt` の握り潰し**を担当する。端末を触る処理は
  必ずこの `with` の中に置く。CLI 側では `__main__.py` の各コマンドが
  これで包んでいる

### ログ

`loguru` のグローバル logger を、`mylog.getLogger()` で名前を付けて使う。
クラスのあるモジュールでは、クラス本体に
`__log = getLogger("BaseTimer")`（アンダースコア 2 つ）を 1 つ置き、
そのクラスのメソッドでは `self.__log.debug(...)` のように呼ぶ
（`base_timer.py` / `progress_bar.py` 参照）。名前修飾で
`self._BaseTimer__log` に解決されるので、子クラスのインスタンスから
親のメソッドを呼んでも親の名前で出る。`_log`（1 つ）だと MRO で
子クラスの定義が勝ち、親のログが子の水準で出てしまうので使わない。
クラスの無いモジュール（`__main__.py` の `main`）は、モジュール先頭に
`_log = getLogger("main")` を置く。

`__init__` の中で `self.__log = ...` はしない。クラス本体に置くことで、
`super().__init__()` を呼び忘れても親のログが `AttributeError` に
ならず、`classmethod` からも使え、インスタンスを作る前から水準が効く。

水準は、普段はクラス本体の `getLogger(name, level)` で指定する。
テストや実行中など外から変えるときだけ `setLevel(name, level)` を使う
（`getLogger()` の `level` 引数は内部で `setLevel()` を呼ぶだけ）。
知らない水準名を渡すと `ValueError` になる。

各 CLI コマンドの先頭で `loggerInit(debug)` を 1 度だけ呼ぶ規約
（`BaseTimer` をライブラリとして使う側も同じ）。`debug` は名前を
指定していないログの既定水準（`DEBUG` / `INFO`）を決める。
`getLogger()` / `setLevel()` で指定した名前ごとの水準は、
呼ぶ順に関わらず `loggerInit()` で上書きされない
（実行時に環境変数で切り替える用途が無いため、TODO-003 で
`TMR_LOG` は廃止した）。

### バージョン

`hatch-vcs` で git タグから決まる。`__init__.py` は
`importlib.metadata.version()` で読み、未インストールなら `"0.0.0"`。
ソースに版番号を書かない。

## テスト

`unittest.mock.patch` で `tmr.base_timer` の `Terminal` / `ProgressBar` /
`click` / `time` を丸ごと差し替えるのが基本形（`tests/test_base_timer.py`
の fixture 参照）。CLI は `click.testing.CliRunner` + `BaseTimer` の
モック（`tests/test_timer.py`）。スレッドが絡む部分だけ実物を動かす
統合テストが `tests/test_integration_alarm.py` にある。

`Terminal` をモックするときは `term.width` に**数値**を入れること
（`display()` が幅と比較するため、MagicMock のままだと落ちる）。

## タスク管理

ソースを直す作業は、着手前に `TODO.md` へ項目を足してから始める。
決着した項目は `archives/todo/TODO-NNN. タイトル.md` へ 1 項目 1 ファイルで
移し、`TODO.md` の「完了済み」に目次として足す。

## 補足

- `TBD.md` と `archives/` 直下の `20260211-*.md` などは、この運用を始める
  前のコードレビュー結果で、**現行の仕様ではない**。実装の根拠として
  参照しない（`archives/todo/` とは別物）
- `README.md` の `timer` サブコマンドの help 出力は古く、実装にある
  `--title` / `--title-color` が載っていない。オプションを変えたら
  README も直す
