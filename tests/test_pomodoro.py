from unittest import mock

from click.testing import CliRunner

from tmr.__main__ import pomodoro


def test_pomodoro_args():
    runner = CliRunner()
    result = runner.invoke(pomodoro, ["--help"])
    assert result.exit_code == 0
    assert "pomodoro" in result.output
    # check default options
    assert "--work-time" in result.output
    assert "--break-time" in result.output
    assert "--long-break-time" in result.output
    assert "--cycles" in result.output


def test_pomodoro_exec():
    """Verify the sequence of timer execution"""
    runner = CliRunner()

    # Mock BaseTimer to prevent actual waiting and capture calls
    with mock.patch("tmr.__main__.BaseTimer") as MockTimer:
        # Helper to simulate timer completion (return True for user interrupt logic)
        instance = MockTimer.return_value

        # We need side_effect to return False (completed normally)
        # so loop continues. If True (interrupted), loop breaks.
        instance.main.side_effect = [False, False, False, True]

        # Run with 2 cycles
        result = runner.invoke(
            pomodoro,
            ["--cycles", "2", "--work-time", "0.1", "--break-time", "0.1"],
        )

        assert result.exit_code == 0

        # Expected calls:
        # Cycle 1: Work -> Short Break
        # Cycle 2: Work -> Long Break
        # Total 4 calls
        assert MockTimer.call_count == 4

        calls = MockTimer.call_args_list

        # Check title arguments for each call
        # calls[i].args[0] is (title, color)

        # 1. Work
        assert calls[0].args[0][0] == "WORK"
        # 2. Short Break
        assert calls[1].args[0][0] == "SHORT_BREAK"
        # 3. Work
        assert calls[2].args[0][0] == "WORK"
        # 4. Long Break (last one in loop logic for i == cycles -1)
        assert calls[3].args[0][0] == "LONG_BREAK"
