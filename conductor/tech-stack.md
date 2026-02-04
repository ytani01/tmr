# Tech Stack: tmr

## Environment
- **Language**: Python >= 3.13
- **Package Manager**: uv
- **Task Runner**: mise

## Core Libraries
- **CLI Framework**: [Click](https://click.palletsprojects.com/) - コマンドライン引数とオプションのパース。
- **Logging**: [Loguru](https://github.com/Delgan/loguru) - シンプルかつ強力な構造化ログ。
- **TUI**: [Rich](https://github.com/Textualize/rich) - リッチなターミナルUI（プログレスバー、スタイルなど）。
- **Standard Libraries**: `time`, `sys`, `threading` (想定)

## Quality & Testing
- **Linter/Formatter**: Ruff (78 char limit)
- **Type Checker**: Mypy, Basedpyright
- **Test Framework**: pytest
- **Build Backend**: hatchling

## Architecture Patterns
- **Entry Point**: `src/tmr/__main__.py`
- **Application Logic**: `src/tmr/app.py` (Object-Oriented approach)
- **Utilities**: `src/tmr/click_utils.py` (Shared CLI options)
