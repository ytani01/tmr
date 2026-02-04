# Style and Conventions

## General
- Follow PEP 8 for Python code style.
- Use `loguru` for logging instead of the standard `logging` module.
- Use `click` for all CLI-related logic.

## Formatting & Linting
- **Ruff**: Primary tool for formatting and linting.
    - Line length: 78 characters (as per `mise.toml`).
    - Format command: `uv run ruff format --line-length 78 src`.
    - Check command: `uv run ruff check --fix --extend-select I src`.
- **Type Hints**: Required and checked via `mypy` and `basedpyright`.
    - Standard type checking mode for `basedpyright`.

## Naming
- Use `snake_case` for functions, variables, and file names.
- Use `PascalCase` for classes.
- Internal package: `tmr`.

## Documentation
- (Implicit) Use docstrings for modules, classes, and functions.
- (Implicit) Follow standard Python documentation conventions.
