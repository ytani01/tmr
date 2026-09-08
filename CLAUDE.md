# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

`tmr` — ターミナル上で動く CLI タイマー（単純タイマー + ポモドーロ）。

## 文書の書き分け

**設計の説明は [`docs/Developer.md`](docs/Developer.md) が正**（TODO-017）。
このファイルには、作業のたびに要る要点と落とし穴だけを置き、詳しい
理由や図はそちらに書く。二重に書かない。

| 文書 | 中身 |
|---|---|
| `CLAUDE.md` | 作業時の要点・落とし穴（このファイル） |
| `README.md` | 概要、インストール、最初の一歩 |
| `docs/User.md` | 全オプション、キー操作、画面の見方、アラーム、設定ファイル |
| `docs/Developer.md` | モジュール構成、設計の意図、テスト、開発コマンド |

## コマンド

```bash
uv run pytest tests                        # テストだけ流す（最速）
uv run tmr timer 1                         # 手元で動かす（1 分）
uv run tmr pomodoro -w 0.1 -b 0.1 -c 2     # ポモドーロを短時間で確認
```

lint の中身（`mise run lint` 相当。個別に流すならこの順）:

```bash
uv run ruff format --line-length 78 src tests
uv run ruff check --fix --extend-select I src tests
uv run basedpyright src tests
uv run mypy src tests
```

**行長は 78 文字**（`pyproject.toml` ではなく `mise.toml` の引数で指定）。

**`mise run test` / `mise run lint` を呼ぶと `upgradeproject` が動き、
`uv.lock` を削除して `uv sync` し直す。** 普段の確認には上の
`uv run ...` を使い、`mise run` はリリース前など意図があるときだけにする。

## 設計の要点

詳細は `docs/Developer.md` の各節にある。ここは索引を兼ねた要約。

- **`Timer` は 3 つに分かれている** — `clock.py` の `TimerClock`（経過
  時間。端末に触らない）、`view.py` の `TimerView`（列の定義・省略・
  スタイル）、`timer.py` の `Timer`（メインループ・キー操作・アラーム）。
  `PomodoroTimer` は `Timer` を**継承せず、順番に呼び出すだけ**
- **フェーズ制御は戻り値 1 つ** — `Timer.main()` は quit で終わった
  ときだけ `True` を返し、`PomodoroTimer.run()` がそれを見て打ち切る。
  `next` は終わらせるが `True` を返さない
- **表示は `TimerView.col_list()` で決まる** — 並び順が画面の並び順、
  `priority` が幅の足りないときに削る順。項目を足すときは `col_list()` に
  1 行足し、`display()` で値を入れる
- **キー割り当ては `Timer.cmd_list()` で決まる** — `keys` に足すだけで
  ヘルプも追随する
- **時刻は `time.monotonic()`** — 早送り・巻き戻し・ポーズは
  `TimerClock.t_start` をずらして表現する（`elapsed` を直接いじらない）
- **値の検証は CLI と dataclass の二重**（`click` の `Range` +
  コールバック、`ValueError`）。ライブラリとして直接使う経路が
  CLI を通らないため。アラームの回数・間隔・`cmd` の扱いは
  `docs/Developer.md`「値の検証」を見る
- **アラームの止め方は 2 通り** — ベルは `alarm_active` フラグ、
  コマンド（`AlarmParams.cmd`）は `stop_alarm_cmd()` がプロセスグループ
  ごとシグナルを送る。**ここが最も込み入っているので、触る前に
  `docs/Developer.md`「アラームのコマンド」を読む**
- **端末を触る処理は `TerminalContext`（`terminal.py`）の `with` の中に
  置く** — カーソルの復帰と `KeyboardInterrupt` の握り潰しを担当する
- **設定ファイルは `ConfigGroup.make_context()` の中で読む** —
  サブコマンドを直接 `invoke()` しても読まれない

### ログの書き方

クラスのあるモジュールでは、**クラス本体に**
`__log = getLogger(__qualname__)`（アンダースコア 2 つ）を 1 つ置き、
メソッドからは `self.__log.debug(...)` と呼ぶ。`__init__` の中で
`self.__log = ...` はしない。クラスの無いモジュール（`cli.py`）は、
モジュール先頭に `_log = getLogger("main")` を置く。
各 CLI コマンドの先頭で `loggerInit(debug)` を 1 度だけ呼ぶ。

アンダースコア 1 つにしない理由、`__qualname__` を使う理由、水準の
決まり方は `docs/Developer.md`「ログ」にある。

### バージョン

`hatch-vcs` で git タグから決まる。**ソースに版番号を書かない。**

## テスト

`unittest.mock.patch` で差し替えるのが基本形。**モジュールごとに
patch 先が違う**ので注意する。

| テスト | patch する先 |
|---|---|
| `tests/test_timer.py` | `tmr.timer` の `Terminal` / `TimerView` / `click` / `time`（アラームの sleep）/ `subprocess`（アラームのコマンド）、`tmr.clock` の `time`（経過時間） |
| `tests/test_view.py` | `tmr.view` の `ProgressBar` / `click`。`Terminal` は `MagicMock` を渡す |
| `tests/test_clock.py` | `tmr.clock` の `time` だけ（端末に依存しない） |

- `Terminal` をモックするときは `term.width` に**数値**を入れること
  （`TimerView.display()` が幅と比較するため、MagicMock のままだと落ちる）
- 設定を絡めたテストは `cli` から呼び、`XDG_CONFIG_HOME` を `tmp_path` に
  向ける（`tests/test_config.py` 参照）
- `tests/conftest.py` が `tmr.timer` の `os.killpg` を常に塞いでいる
  （autouse）。呼び出しを見たいテストは `mock_killpg` を使う

## 補足

- **オプションを変えたら `README.md` と `docs/User.md` の help 出力も直す**
- `archives/` 直下の `20260211-*.md` などは、この運用を始める前の
  コードレビュー結果で、**現行の仕様ではない**。実装の根拠として
  参照しない（`archives/todo/` とは別物）
