# Task Completion Checklist

Before considering a task complete, ensure the following steps are performed:

1. **Code Quality**:
    - [ ] Run `mise run lint` to ensure formatting and type checking pass.
    - [ ] Verify that no new Ruff warnings are introduced.

2. **Testing**:
    - [ ] Run `mise run test` to execute all tests.
    - [ ] Ensure all tests pass.
    - [ ] Add new tests for any new functionality or bug fixes.

3. **Functionality**:
    - [ ] Manually verify the changes by running `uv run tmr` with relevant arguments.

4. **Standards**:
    - [ ] Run `./check_init.sh` if any changes were made to initialization logic (as per global instructions, though not explicitly found in this project yet, it's a good practice if it exists).
    - [ ] (Self-Check) Ensure all `plan.md` items (if a plan exists) are checked and documented.
