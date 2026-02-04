# Suggested Commands

## Running the Application
- `uv run tmr`: Execute the main CLI entrypoint.
- `uv run tmr --help`: Show help message.

## Development Tasks (using mise)
- `mise run lint`: Run Ruff (format & check), Basedpyright, and Mypy.
- `mise run test`: Run tests using Pytest (includes linting by dependency).
- `mise run build`: Build the project (includes testing by dependency).
- `mise run uppj`: Upgrade project dependencies and sync `uv.lock`.

## Standard uv Commands
- `uv sync`: Sync dependencies.
- `uv add <package>`: Add a new dependency.
- `uv run <command>`: Run a command in the project environment.
