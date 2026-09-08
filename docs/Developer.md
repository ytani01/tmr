# tmr の内部構造

手を入れる人向けの説明。
使い方は [docs/User.md](User.md) にあります。


## == 開発環境

普段の確認は `uv run` で足ります。

```bash
uv run pytest tests                        # テストだけ流す（最速）
uv run tmr timer 1                         # 手元で動かす（1 分）
uv run tmr pomodoro -w 0.1 -b 0.1 -c 2     # ポモドーロを短時間で確認
```

lint はこの 4 本です。

```bash
uv run ruff format --line-length 78 src tests
uv run ruff check --fix --extend-select I src tests
uv run basedpyright src tests
uv run mypy src tests
```

**行長は 78 文字**。`pyproject.toml` ではなく `mise.toml` の引数で
指定しています。

`mise` のタスクは `build` → `test` → `lint` → `upgradeproject` と
`depends` でつながっています。**`mise run test` や `mise run lint` を
呼ぶと `upgradeproject` が動き、`uv.lock` を削除して `uv sync` を
やり直します。** 普段は上の `uv run` を使い、`mise run` は
リリース前など意図があるときだけにしてください。


## == モジュール構成

```mermaid
flowchart TD
    CLI["cli.py<br/>click のコマンド定義"] --> T["Timer<br/>メインループ・キー操作・アラーム"]
    CLI --> P["PomodoroTimer<br/>フェーズを順に回すだけ"]
    P -. "フェーズごとに生成して main() を呼ぶ<br/>（継承しない）" .-> T
    T --> C["TimerClock<br/>経過時間（端末に触らない）"]
    T --> V["TimerView<br/>列の定義・省略・スタイル"]
    T --> TERM["Terminal (blessed)<br/>キー入力・幅"]
    V --> PB["ProgressBar"]
    V --> TERM
```

| ファイル | 役割 |
|---|---|
| `cli.py` | `click` のコマンド定義。オプションの検証と秒への換算 |
| `config.py` | 設定ファイルを読んで `default_map` を作る `ConfigGroup` |
| `timer.py` | `Timer`（メインループ、キー操作、アラーム）と `AlarmParams` |
| `clock.py` | `TimerClock`。経過時間だけを持つ |
| `view.py` | `TimerView`（列の定義・省略・スタイル）と `TimerTitle` |
| `progress_bar.py` | `ProgressBar`。バーの文字列を作る |
| `pomodoro.py` | `PomodoroTimer`、`PomodoroConfig`、`phases()` |
| `terminal.py` | `TerminalContext` とエスケープシーケンスの定数 |
| `timefmt.py` | 時間の単位と `t_str()` |
| `mylog.py` | `loguru` に名前と水準を足す薄い層 |
| `click_utils.py` | 全コマンド共通のオプション（`-V` / `-d` / `-h`） |


## == なぜ 3 つに分けたか

もとは `Timer` 1 クラスに全部が入っていました。今は 3 つです。

- `TimerClock` — 経過時間。**端末に触らないので単体で試せる**。
  早送り・ポーズのテストに `blessed` が要りません
- `TimerView` — 列の定義、幅に応じた省略、スタイル付け。
  「何を出すか」を変えたいときはここだけ見ればよい
- `Timer` — メインループとキー操作・アラーム。`Terminal` を作り、
  上の 2 つを持つ

分ける前は、表示の桁を直したいときでも、キー入力の処理を読まなければ
なりませんでした。テストも `Terminal` のモックなしには何も書けません
でした。


## == `PomodoroTimer` が `Timer` を継承しない理由

`PomodoroTimer` は `Timer` の**使い手**であって、「特殊な `Timer`」では
ないからです。

ポモドーロがやることは、`phases()` が返すフェーズを順に取り出し、
そのたびに `Timer` を作って `main()` を呼ぶ、それだけです。
`Timer` のメインループもキー操作も上書きしません。
継承すると「どのメソッドを上書きしてよいか」という制約が増えるだけで、
得るものがありません。

`phases()` はジェネレータで、**フェーズを無限に返します**。
`cycles` は「長い休憩までの作業回数」という 1 巡の長さで、
巡回そのものは終わりません。終わらせるのは `run()` 側の判断です。


## == メインループとフェーズ制御

`Timer.main()` は `term.cbreak()` の中で `inkey(timeout=0.2)` を
回します。**この 0.2 秒がそのまま画面の更新間隔**です。

```mermaid
stateDiagram-v2
    [*] --> Running: clock.start()
    Running --> Running: inkey 0.2 秒 → tick → display
    Running --> Paused: P / SPACE
    Paused --> Running: P / SPACE
    Running --> Alarm: is_timeup かつポーズ中でない
    Alarm --> Done: 任意のキー、または鳴り終わり
    Running --> Done: N next（enable_next のときだけ）
    Running --> Done: Q quit
    Done --> [*]
```

サイクル全体を止めるかどうかは、`main()` の**戻り値 1 つ**で決まります。

```mermaid
flowchart LR
    M["Timer.main()"] --> Q{"quit で終わった?"}
    Q -- "はい（True）" --> STOP["PomodoroTimer.run() が<br/>サイクルごと打ち切る"]
    Q -- "いいえ（False）" --> NEXT["次のフェーズへ"]
```

`main()` が `True` を返すのは、**quit コマンドで終わったときだけ**です。
`next` はタイマーを終わらせますが `True` を返しません。
**この 1 点だけがポモドーロの制御経路**です。

`next` は `enable_next=True` のときしか効きません
（`PomodoroTimer._run_timer()` がこれを渡します）。
`fn_help()` も `enable_next` を見て、単純タイマーでは `Next` の行を
出しません。


## == 表示の決まり方

`TimerView.col_list()` が返すリストが表示のすべてを決めます。

- **リストの並び順が、そのまま画面上の並び順**
- 各 `TimerCol` の **`priority` が、幅の足りないときに削る順**
  （小さいものから削られる）

```mermaid
flowchart TD
    A["col_list()<br/>並び = 表示順 / priority = 削る順"] --> B["display() が各列に値を入れる"]
    B --> C{"合計幅 > 端末幅?"}
    C -- "はい" --> D["priority の小さい列から use=False"]
    D --> C
    C -- "いいえ" --> E["残った幅を pbar に割り当てる"]
    E --> F["click.style() で色・太字・点滅を付けて 1 行出力"]
```

現在の定義:

| 表示順 | name | priority | 中身 |
|---|---|---|---|
| 1 | `date` | 1 | `2026-09-08` |
| 2 | `time` | 2 | `14:03:21` |
| 3 | `title` | 8 | `-t` で指定したタイトル（太字） |
| 4 | `limit` | 5 | 設定時間 `25m` |
| 5 | `state` | 7 | `[PAUSE]` / `[TIME UP]`。それ以外は空 |
| 6 | `rate` | 4 | ` 42.0%` |
| 7 | `elapsed` | 3 | 経過 `10m30s` |
| 8 | `pbar` | 6 | プログレスバー（残った幅を全部使う） |
| 9 | `remain` | 9 | 残り `14m30s` |

`pbar` は幅の計算中だけ `PBAR_LEN_MIN`（10 文字）分の仮の値を持ち、
残す列が決まってから実際の長さで作り直します。
削った結果 1 つも残らなければ `!?` だけを点滅表示します。

`rate_color=True` の列は経過率で色が変わり（`PERCENT_COLOR`）、
`pause_blink=True` の列はポーズ中に点滅します。

**表示項目を足すときは、`col_list()` に 1 行足し、`display()` で
その列に値を入れます。**`title` のように `__init__` で値が決まる
ものは `display()` に足す必要がありません。


## == 時刻の扱い

- 時刻は `time.monotonic()`。NTP でシステム時刻が動いても狂いません
- **早送り・巻き戻し・ポーズは `TimerClock.t_start` をずらして
  表現します**（`elapsed` を直接いじらない）。
  ポーズ中は `t_start = t_cur - elapsed` を毎周回し直すことで、
  経過時間を止めます
- 秒数を `"1h01m01s"` のような文字列にする `t_str()` と、
  時間の単位（`SEC_MIN` / `MIN_HOUR`）は `timefmt.py` にあります


## == 値の検証

0 以下・`nan`・`inf` の時間やサイクル数は、二重に弾いています。

- CLI では `click.IntRange` / `click.FloatRange` と、
  `nan` / `inf` を弾くコールバック
- `TimerClock` / `PomodoroConfig` / `AlarmParams` の `ValueError`

`Timer` や `PomodoroTimer` をライブラリとして直接使う経路は CLI を
通らないので、両方が要ります。

**ただしアラームの回数と間隔は 0 を許します**（鳴らさない／間を
空けない）。間隔の上限は 1 日（`timefmt.SEC_DAY`）で、
`time.sleep()` が `OverflowError` にならないようにするためです。


## == ログ

`loguru` のグローバル logger を、`mylog.getLogger()` で名前を付けて
使います。詳しい使い方は `mylog.py` の docstring にあります。

クラスのあるモジュールでは、**クラス本体に**
`__log = getLogger(__qualname__)`（アンダースコア 2 つ）を 1 つ置き、
メソッドからは `self.__log.debug(...)` と呼びます。

- `__qualname__` はクラス本体の実行前に暗黙で入る変数で、クラス名が
  そのまま入ります。クラス名を手で書かずに済み、改名してもずれません
- アンダースコア 2 つなら名前修飾で `self._Timer__log` に解決されるので、
  子クラスのインスタンスから親のメソッドを呼んでも親の名前で出ます。
  `_log`（1 つ）だと MRO で子クラスの定義が勝ち、親のログが子の水準で
  出てしまいます
- `__init__` の中で `self.__log = ...` はしません。クラス本体に置けば、
  `super().__init__()` を呼び忘れても `AttributeError` にならず、
  `classmethod` からも使え、インスタンスを作る前から水準が効きます

クラスの無いモジュール（`cli.py`）は、モジュール先頭に
`_log = getLogger("main")` を置きます。

水準は、普段はクラス本体の `getLogger(name, level)` で指定します。
テストや実行中など外から変えるときだけ `setLevel(name, level)` を
使い、既定に戻すには `setLevel(name)` を呼びます。

各 CLI コマンドの先頭で `loggerInit(debug)` を 1 度だけ呼びます。
`debug` が決めるのは、名前を指定していないログの既定水準
（`DEBUG` / `INFO`）だけです。`getLogger()` / `setLevel()` で
指定した名前ごとの水準は、呼ぶ順に関わらず `loggerInit()` で
上書きされません。


## == 端末の後始末

`TerminalContext`（`terminal.py`）が、**カーソルの復帰と
`KeyboardInterrupt` の握り潰し**を担当します。
端末を触る処理は必ずこの `with` の中に置いてください。
`cli.py` の各コマンドがこれで包んでいます。

アラームは daemon スレッドで `\a` を鳴らします。停止の合図は
`alarm_active` フラグ 1 つで、スレッド側もメインループ側も見ています。


## == 設定ファイルの読み込み

`config.py` が `~/.config/tmr/config.toml`（`XDG_CONFIG_HOME` が
あればその下）を読み、`click` の `default_map` を作ります。
優先順位 **コマンドライン引数 > 設定ファイル > コードの既定値** は
`click` 側が面倒を見るので、各コマンドの定義には手を入れていません。

`cli` は `ConfigGroup`（`click.Group` の子）で、`make_context()` の
中で設定を読みます。**サブコマンドを直接 `invoke()` しても設定は
読まれません。** 設定を絡めたテストは `cli` から呼び、
`XDG_CONFIG_HOME` を `tmp_path` に向けてください
（`tests/test_config.py` 参照）。

`default_map` は別名にも同じ dict を張るので、`tmr t` でも `[timer]`
が効きます。

`config.py` は `loggerInit()` より前に動くので**ログを出しません**
（`loguru` の既定ハンドラに素通しされ、毎回出てしまうため）。
読んだ結果は `cli` の中で `ctx.default_map` として出します。


## == テスト

`unittest.mock.patch` で差し替えるのが基本形です。
**モジュールごとに patch する先が違う**ので注意してください。

| テスト | patch する先 |
|---|---|
| `tests/test_timer.py` | `tmr.timer` の `Terminal` / `TimerView` / `click` / `time`（アラームの sleep）、`tmr.clock` の `time`（経過時間） |
| `tests/test_view.py` | `tmr.view` の `ProgressBar` / `click`。`Terminal` は `MagicMock` を渡す |
| `tests/test_clock.py` | `tmr.clock` の `time` だけ（端末に依存しない） |

CLI は `click.testing.CliRunner` と `Timer` のモックで試します
（`tests/test_cli.py`）。スレッドが絡む部分だけ実物を動かす
統合テストが `tests/test_integration_alarm.py` にあります。

`Terminal` をモックするときは、**`term.width` に数値を入れて
ください**（`TimerView.display()` が幅と比較するので、`MagicMock`
のままだと落ちます）。


## == バージョン

`hatch-vcs` で git タグから決まります。`__init__.py` は
`importlib.metadata.version()` で読み、未インストールなら `"0.0.0"`
です。**ソースに版番号を書かないでください。**
