# TODO-009 実装依頼（implementer）

## 目的

`src/tmr/` のモジュール構成を整理する。**移動と改名だけで、挙動は変えない。**

## やること

### 1. `base_timer.py` → `timer.py`、`BaseTimer` → `Timer`

- `git mv src/tmr/base_timer.py src/tmr/timer.py`
- クラス名 `BaseTimer` を `Timer` に改名。docstring の `Base Timer.` も直す
- 参照元（`pomodoro.py`、テスト）も追随

### 2. `utils.py` → `terminal.py`

- `git mv src/tmr/utils.py src/tmr/terminal.py`
- `__init__.py` にある `ESC` / `ESQ_CSR_ON` / `ESQ_CSR_OFF` / `ESQ_EL0` /
  `ESQ_EL1` / `ESQ_EL2` の定義を `terminal.py` へ移す（コメントも一緒に）
- `ESQ_EL0` / `ESQ_EL1` は本体から使わないが**残す**（ライブラリ利用者向け。
  2026-09-08 に決めた）
- `timer.py` は `from .terminal import ESQ_EL2` で取る

### 3. `timefmt.py` を新設

- `SEC_MIN` / `MIN_HOUR` を `__init__.py` から `timefmt.py` へ移す
- `Timer.display()` 内のローカル関数 `t_str()` を `timefmt.py` の
  モジュール関数に出す（名前・引数・戻り値はそのまま）
- `display()` からは `t_str(...)` を呼ぶだけにする
- `cli.py` の `SEC_MIN` も `from .timefmt import SEC_MIN` に

### 4. `__init__.py` は `__version__` だけにする

- `from loguru import logger` の再輸出も消す（どこからも使われていない）
- `__all__` は `["__version__"]` だけにするか、`__all__` 自体を消す（任せる）

### 5. `cli.py` を新設

- `__main__.py` の click コマンド定義（`cli` / `timer` / `pomodoro` と
  `add_command`）を丸ごと `src/tmr/cli.py` へ移す
- `__main__.py` は `python -m tmr` の入口だけにする:

  ```python
  from .cli import cli

  if __name__ == "__main__":
      cli()
  ```

- `pyproject.toml` の `[project.scripts]` を `tmr = "tmr.cli:cli"` に変える

### 6. テストのファイル名と import

**ファイル名がぶつかるので、この順で `git mv` すること。**

- `tests/test_timer.py`（CLI の `timer` コマンドを試すもの）→ `tests/test_cli.py`
  - import を `from tmr.cli import timer` に
- `tests/test_base_timer.py` → `tests/test_timer.py`
  - import を `from tmr.timer import Timer` に。モックの
    `patch("tmr.base_timer....")` は `patch("tmr.timer....")` に
- `tests/test_utils.py` → `tests/test_terminal.py`
  - import を `from tmr.terminal import ...` に
- `tests/test_integration_alarm.py`、`tests/test_pomodoro.py`、
  `tests/test_config.py` の import も追随
  （`from tmr.__main__ import cli` → `from tmr.cli import cli`）
- `tests/test_timefmt.py` を新設し、`t_str()` の単体テストを書く。
  分単位（秒あり／`omit_sec` で秒省略）、時間単位、0 秒、境界（59 秒→60 秒）を見る

### 7. 文書

- `CLAUDE.md` の「設計」以下、`base_timer.py` / `BaseTimer` / `utils.py` /
  `__main__.py` を指している記述を新しい名前に直す。`timefmt.py` の役割も 1 行足す
- `README.md` にモジュール名の記述があれば直す（無ければ何もしない）

## 完了条件

- `uv run pytest tests` が全部通る
- lint が通る（この順で）:
  ```
  uv run ruff format --line-length 78 src tests
  uv run ruff check --fix --extend-select I src tests
  uv run basedpyright src tests
  uv run mypy src tests
  ```
- `uv run tmr timer 1` と `uv run tmr pomodoro -w 0.1 -b 0.1 -c 2` が
  起動する（`q` で抜ける。起動確認だけでよい）
- `git status` に残骸ファイルが無い（`git mv` を使うこと）

## 禁止

- 挙動を変えない。ロジックの改善・整理は**しない**（それは TODO-010）
- コミットしない（管理者が行う）

## 報告

`archives/agents/TODO-009/implementer-report.md` に書く。
変更したファイル、検証の結果、判断が要る点。
返事は 5 行以内（終わったか・報告ファイルのパス・判断が要る点）。
