from unittest import mock

from click.testing import CliRunner

from tmr.__main__ import pomodoro
from tmr.pomodoro import PomodoroConfig, PomodoroCore


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


def test_pomodoro_core_run():
    """Verify PomodoroCore logic"""
    config = PomodoroConfig(
        work_sec=0.1,
        break_sec=0.1,
        long_break_sec=0.1,
        cycles=2,
    )
    core = PomodoroCore(config)

    # Mock _run_timer to avoid actual sleep and user input
    # 4 calls expected for 2 cycles: Work, ShortBreak, Work, LongBreak
    # We want to simulate a Quit on the last call to exit the infinite loop
    with mock.patch.object(core, "_run_timer") as mock_run_timer:
        mock_run_timer.side_effect = [False, False, False, True]

        Quit = core.run()

        assert Quit is True
        assert mock_run_timer.call_count == 4

        calls = mock_run_timer.call_args_list
        # 1. Work
        assert calls[0].args[0] == "WORK"
        # 2. Short Break
        assert calls[1].args[0] == "SHORT_BREAK"
        # 3. Work
        assert calls[2].args[0] == "WORK"
        # 4. Long Break (last one in loop logic for i == cycles -1)
        assert calls[3].args[0] == "LONG_BREAK"


def test_pomodoro_cli_exec():
    """Verify CLI command invokes PomodoroCore correctly"""
    runner = CliRunner()

    with mock.patch("tmr.__main__.PomodoroCore") as MockCore:
        instance = MockCore.return_value
        instance.run.return_value = True  # Simulate quit

        result = runner.invoke(
            pomodoro,
            ["--cycles", "2", "--work-time", "0.1", "--break-time", "0.1"],
        )

        assert result.exit_code == 0

        # Verify PomodoroCore initialized with correct config
        assert MockCore.call_count == 1
        config_arg = MockCore.call_args[0][0]
        assert isinstance(config_arg, PomodoroConfig)
        assert config_arg.cycles == 2
        # Verify run called
        instance.run.assert_called_once()
