# TODO-009 implementer 報告

## 変更したファイル

### ソース

- `src/tmr/timer.py`（`git mv base_timer.py timer.py`）
  - クラス `BaseTimer` → `Timer`（`timer.py:39`）、docstring
    `"Base Timer."` → `"Timer."`
  - import を `from .terminal import ESQ_EL2` /
    `from .timefmt import t_str` に変更（`timer.py:1-`）
  - `display()` 内のローカル関数 `t_str()` を削除し、
    `timefmt.t_str()` をそのまま呼ぶだけにした
- `src/tmr/terminal.py`（`git mv utils.py terminal.py`）
  - `ESC` / `ESQ_CSR_ON` / `ESQ_CSR_OFF` / `ESQ_EL0` / `ESQ_EL1` /
    `ESQ_EL2` の定義とコメントを `__init__.py` から移設
    （`terminal.py:6-11`）
- `src/tmr/timefmt.py`（新設）
  - `SEC_MIN` / `MIN_HOUR` と、モジュール関数 `t_str()`
    （旧 `base_timer.py` のローカル関数と同一の実装）
- `src/tmr/__init__.py`
  - `__version__` の定義だけに整理。`SEC_MIN` / `MIN_HOUR` /
    `ESC` 系の定数、`from loguru import logger` の再輸出を削除
  - `__all__ = ["__version__"]`
- `src/tmr/cli.py`（新設）
  - 旧 `__main__.py` の click コマンド定義（`cli` / `timer` /
    `pomodoro` と `add_command`）をそのまま移設
  - import を `.timer.Timer`、`.terminal.TerminalContext`、
    `.timefmt.SEC_MIN` に変更
- `src/tmr/__main__.py`
  - `python -m tmr` の入口だけに縮小（`from .cli import cli` +
    `if __name__ == "__main__": cli()`）
- `src/tmr/pomodoro.py`
  - `from .base_timer import BaseTimer` → `from .timer import Timer`、
    `_run_timer()` 内の生成とコメントを `Timer` に追随
- `pyproject.toml`
  - `[project.scripts]` を `tmr = "tmr.cli:cli"` に変更

### テスト

- `git mv tests/test_timer.py tests/test_cli.py`
  - import を `from tmr.cli import timer` に、
    `mock.patch("tmr.__main__.BaseTimer")` を
    `mock.patch("tmr.cli.Timer")` に変更
- `git mv tests/test_base_timer.py tests/test_timer.py`
  - `BaseTimer` → `Timer`、`base_timer`（フィクスチャ名・パス）→
    `timer` / `tmr.timer` に全置換（`sed` で機械的に置換し、
    目視確認と ruff format 済み）
- `git mv tests/test_utils.py tests/test_terminal.py`
  - import を `from tmr.terminal import ...` に変更
- `tests/test_integration_alarm.py`
  - `from tmr.base_timer import BaseTimer` →
    `from tmr.timer import Timer`、`patch("tmr.base_timer...")` →
    `patch("tmr.timer...")`、ローカル変数名も `timer` に統一
- `tests/test_config.py`
  - `from tmr.__main__ import cli` → `from tmr.cli import cli`、
    `tmr.__main__.BaseTimer` / `tmr.__main__.PomodoroTimer` を
    `tmr.cli.Timer` / `tmr.cli.PomodoroTimer` に変更
- `tests/test_pomodoro.py`
  - `from tmr.__main__ import pomodoro` → `from tmr.cli import pomodoro`、
    `tmr.__main__.PomodoroTimer` → `tmr.cli.PomodoroTimer`、
    `tmr.pomodoro.BaseTimer` → `tmr.pomodoro.Timer`
- `tests/test_timefmt.py`（新設）
  - `t_str()` の単体テスト。分単位（秒あり／`omit_sec` で秒省略、
    秒が残る場合は省略しない）、時間単位（秒あり・`omit_sec`）、
    0 秒、境界（59 秒→60 秒）を確認

### 文書

- `CLAUDE.md`
  - 「BaseTimer が本体」節見出しと本文を `Timer` / `timer.py` に更新
  - `utils.py` → `terminal.py`、`__main__.py` の各コマンド → `cli.py`
    に更新
  - ログの節: `base_timer.py` → `timer.py`、
    `self._BaseTimer__log` → `self._Timer__log`、
    `__main__.py` の `main` → `cli.py` に更新
  - テストの節: `tmr.base_timer` → `tmr.timer`、
    `tests/test_base_timer.py` → `tests/test_timer.py`、
    CLI のテストは `tests/test_cli.py` に更新
  - 「表示は 2 つのリストで決まる」節に `timefmt.py` の役割を 1 行追加
- `README.md`
  - `base_timer` / `utils.py` / `BaseTimer` / `__main__` への言及が
    無かったため変更なし

## 検証結果

すべて成功（終了コード 0）。

- `uv run pytest tests -q` → 74 passed
- `uv run ruff format --line-length 78 src tests` → 変更なし（既に整形済み）
- `uv run ruff check --fix --extend-select I src tests` → All checks passed!
- `uv run basedpyright src tests` → 0 errors, 0 warnings, 0 notes
- `uv run mypy src tests` → Success: no issues found in 20 source files
- `uv run tmr timer 1`（`< /dev/null` 経由、5 秒 timeout）→ 起動して
  プログレスバー表示を確認
- `uv run tmr pomodoro -w 0.1 -b 0.1 -c 2`（同様）→ 起動して
  WORK フェーズの表示を確認
- `git status` → 残骸ファイル無し（`git mv` の追跡どおり）

## 判断が要る点・懸念

- 特になし。移動と改名のみで挙動は変えていない
  （ロジックの整理は TODO-010 の範囲）
- `src/tmr/mylog.py` の docstring 中に例として
  `getLogger("BaseTimer")` という文字列が残っている
  （`mylog.py:80` 付近）。これは実在するクラス名の参照ではなく
  サンプルコード中の例示名なので、指示の「参照元」には当たらないと
  判断し、変更しなかった。必要なら別途指示してほしい
