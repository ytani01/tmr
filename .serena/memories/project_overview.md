# Pomodoro CLI Project Overview

## Purpose
A command-line Pomodoro timer application.

## Tech Stack
- **Language**: Python (>=3.13)
- **CLI Framework**: [Click](https://click.palletsprojects.com/)
- **Logging**: [Loguru](https://github.com/Delgan/loguru)
- **Dependency Management**: [uv](https://github.com/astral-sh/uv)
- **Task Runner**: [mise](https://mise.jdx.dev/)
- **Linting/Formatting**: [Ruff](https://github.com/astral-sh/ruff), [Mypy](https://mypy-lang.org/), [Basedpyright](https://github.com/detachhead/basedpyright)
- **Testing**: [Pytest](https://pytest.org/)

## Codebase Structure
- `src/tmr/`: Main package.
    - `__main__.py`: Entrypoint for the CLI.
    - `app.py`: Main application logic.
    - `click_utils.py`: CLI utilities.
    - `mylog.py`: Logging setup.
- `tests/`: Unit and integration tests.
- `pyproject.toml`: Project metadata and dependencies.
- `mise.toml`: Task definitions for development.
