# TODO-014 実装依頼（implementer）

リポジトリ: /home/ytani/work/tmr（branch: develop）

## 目的

`pomodoro.py` をログ規約に合わせ、`TimerView.display()` の点滅表示に
テストを足す。**挙動は変えない。**

## 作業 1: `src/tmr/pomodoro.py` のログ

`CLAUDE.md` の「ログ」の節に従う。

- `PomodoroTimer` のクラス本体に `__log = getLogger(__qualname__)` を置き、
  `__init__` / `run()` / `_run_timer()` に `self.__log.debug(...)` を足す
- `phases()` はクラスの外なので、モジュール先頭に
  `_log = getLogger("pomodoro")` を置いて `_log.debug(...)` を使う
- ログの粒度と書き方は `src/tmr/clock.py` に合わせる
  （`self.__log.debug(f"t_limit={t_limit}")` のように引数を出す。
  引数が無いところは `debug("")`）
- `PomodoroConfig.__post_init__` の検証エラーにはログを足さない
  （例外で十分）

## 作業 2: 点滅表示のテスト（`tests/test_view.py`）

`TimerView.display()` の点滅に、直接のテストが無い。次の 2 件を足す。

- `pause_blink=True` の列が、ポーズ中に `click.secho(..., blink=True)`
  で出ること
- `state` 列が、満了時（`clock.is_timeup`）に `blink=True` で出ること

`src/tmr/view.py` の 183〜196 行あたりが対象。既存の
`test_display_pause_state` / `test_display_timeup_state` は `value` しか
見ていないので、その隣に足す。patch 先とフィクスチャは既存の
`tests/test_view.py` の書き方に揃えること（`tmr.view` の
`ProgressBar` / `click` を patch、`Terminal` は `MagicMock` で
`term.width` に数値）。

## 完了条件

```bash
uv run pytest tests
uv run ruff format --line-length 78 src tests
uv run ruff check --fix --extend-select I src tests
uv run basedpyright src tests
uv run mypy src tests
```

がすべて通ること。行長は 78 文字。

## 報告

`archives/agents/TODO-014/implementer-report.md` に、変更点・検証結果・
残る懸念を書く。返事は「終わったか・報告ファイルのパス・判断が要る点」の
5 行以内。
