from unittest import mock

from click.testing import CliRunner

from tmr.__main__ import pomodoro
from tmr.pomodoro import PomodoroConfig, PomodoroTimer


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


def test_pomodoro_timer_run():
    """Verify PomodoroTimer logic"""
    config = PomodoroConfig(
        work_sec=0.1,
        break_sec=0.1,
        long_break_sec=0.1,
        cycles=2,
    )
    timer = PomodoroTimer(config)

    # Mock _run_timer to avoid actual sleep and user input
    # 4 calls expected for 2 cycles: Work, ShortBreak, Work, LongBreak
    # We want to simulate a Quit on the last call to exit the infinite loop
    with mock.patch.object(timer, "_run_timer") as mock_run_timer:
        mock_run_timer.side_effect = [False, False, False, True]

        Quit = timer.run()

        assert Quit is True
        assert mock_run_timer.call_count == 4

        calls = mock_run_timer.call_args_list
        # 1. Work
        assert calls[0].args[0] == "WORK       "
        # 2. Short Break
        assert calls[1].args[0] == "SHORT_BREAK"
        # 3. Work
        assert calls[2].args[0] == "WORK       "
        # 4. Long Break (last one in loop logic for i == cycles -1)
        assert calls[3].args[0] == "LONG_BREAK "


def test_pomodoro_cli_exec():
    """Verify CLI command invokes PomodoroTimer correctly"""
    runner = CliRunner()

    with mock.patch("tmr.__main__.PomodoroTimer") as MockTimer:
        instance = MockTimer.return_value
        instance.run.return_value = True  # Simulate quit

        result = runner.invoke(
            pomodoro,
            ["--cycles", "2", "--work-time", "0.1", "--break-time", "0.1"],
        )

        assert result.exit_code == 0

        # Verify PomodoroTimer initialized with correct config
        assert MockTimer.call_count == 1
        config_arg = MockTimer.call_args[0][0]
        assert isinstance(config_arg, PomodoroConfig)
        assert config_arg.cycles == 2
        # Verify run called
        instance.run.assert_called_once()


def test_pomodoro_timer_quit_in_work():
    """Verify PomodoroTimer quits correctly during Work"""
    config = PomodoroConfig(
        work_sec=0.1,
        break_sec=0.1,
        long_break_sec=0.1,
        cycles=2,
    )
    timer = PomodoroTimer(config)

    with mock.patch.object(timer, "_run_timer") as mock_run_timer:
        # 1st call (WORK) returns True (Quit)
        mock_run_timer.side_effect = [True]

        Quit = timer.run()

        assert Quit is True
        assert mock_run_timer.call_count == 1
        assert mock_run_timer.call_args[0][0] == "WORK       "


def test_pomodoro_timer_quit_in_short_break():
    """Verify PomodoroTimer quits correctly during Short Break"""
    config = PomodoroConfig(
        work_sec=0.1,
        break_sec=0.1,
        long_break_sec=0.1,
        cycles=2,
    )
    timer = PomodoroTimer(config)

    with mock.patch.object(timer, "_run_timer") as mock_run_timer:
        # 1. Work -> False
        # 2. Short Break -> True (Quit)
        mock_run_timer.side_effect = [False, True]

        Quit = timer.run()

        assert Quit is True
        assert mock_run_timer.call_count == 2

        calls = mock_run_timer.call_args_list
        assert calls[0].args[0] == "WORK       "
        assert calls[1].args[0] == "SHORT_BREAK"


def test_pomodoro_timer_run_timer():
    """Verify _run_timer implementation calls BaseTimer"""
    config = PomodoroConfig(
        work_sec=0.1,
        break_sec=0.1,
        long_break_sec=0.1,
        cycles=1,
    )
    timer = PomodoroTimer(config)

    with mock.patch("tmr.pomodoro.BaseTimer") as MockTimer:
        instance = MockTimer.return_value
        instance.main.return_value = True  # Quit

        # Call _run_timer directly
        ret = timer._run_timer("TEST", 10.0, "white")

        assert ret is True
        MockTimer.assert_called_once()
        args = MockTimer.call_args
        assert args[0][0] == ("TEST", "white")
        assert args[0][1] == 10.0
        assert args[1]["enable_next"] is True
        instance.main.assert_called_once()
