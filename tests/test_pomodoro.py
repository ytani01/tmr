import dataclasses
from unittest import mock

import pytest
from click.testing import CliRunner

from tmr.cli import pomodoro
from tmr.pomodoro import PomodoroConfig, PomodoroTimer, phases
from tmr.view import TimerTitle


@pytest.mark.parametrize(
    "field,value",
    [
        ("work_sec", 0),
        ("work_sec", -1),
        ("work_sec", float("nan")),
        ("work_sec", float("inf")),
        ("break_sec", 0),
        ("break_sec", -1),
        ("break_sec", float("nan")),
        ("break_sec", float("inf")),
        ("long_break_sec", 0),
        ("long_break_sec", -1),
        ("long_break_sec", float("nan")),
        ("long_break_sec", float("inf")),
        ("cycles", 0),
        ("cycles", -1),
    ],
)
def test_pomodoro_config_invalid_field_raises(field, value):
    """各フィールドが不正なら PomodoroConfig の構築時に ValueError。"""
    work_sec = value if field == "work_sec" else 10.0
    break_sec = value if field == "break_sec" else 20.0
    long_break_sec = value if field == "long_break_sec" else 30.0
    cycles = value if field == "cycles" else 2

    with pytest.raises(ValueError):
        PomodoroConfig(
            work_sec=work_sec,
            break_sec=break_sec,
            long_break_sec=long_break_sec,
            cycles=cycles,
        )


def test_pomodoro_config_is_frozen():
    """構築後の代入は FrozenInstanceError になる。"""
    config = PomodoroConfig(
        work_sec=10.0,
        break_sec=20.0,
        long_break_sec=30.0,
        cycles=2,
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        config.cycles = 0  # type: ignore[misc]


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


def test_phases_one_cycle():
    """フェーズの並び・色・秒数（最初の 1 サイクル分）。"""
    config = PomodoroConfig(
        work_sec=10.0,
        break_sec=20.0,
        long_break_sec=30.0,
        cycles=2,
    )
    gen = phases(config)
    got = [next(gen) for _ in range(4)]

    assert got[0] == (TimerTitle("WORK:1/2", "cyan", 16), 10.0)
    assert got[1] == (TimerTitle("SHORT_BREAK:1/2", "yellow", 16), 20.0)
    assert got[2] == (TimerTitle("WORK:2/2", "cyan", 16), 10.0)
    assert got[3] == (TimerTitle("LONG_BREAK:2/2", "red", 16), 30.0)


def test_phases_repeats():
    """サイクルを繰り返す。"""
    config = PomodoroConfig(
        work_sec=10.0,
        break_sec=20.0,
        long_break_sec=30.0,
        cycles=1,
    )
    gen = phases(config)
    got = [next(gen) for _ in range(4)]

    assert got[0] == (TimerTitle("WORK:1/1", "cyan", 16), 10.0)
    assert got[1] == (TimerTitle("LONG_BREAK:1/1", "red", 16), 30.0)
    assert got[2] == got[0]
    assert got[3] == got[1]


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
        assert calls[0].args[0].display_text == "WORK:1/2        "
        # 2. Short Break
        assert calls[1].args[0].display_text == "SHORT_BREAK:1/2 "
        # 3. Work
        assert calls[2].args[0].display_text == "WORK:2/2        "
        # 4. Long Break (last one in loop logic for i == cycles -1)
        assert calls[3].args[0].display_text == "LONG_BREAK:2/2  "


def test_pomodoro_cli_exec():
    """Verify CLI command invokes PomodoroTimer correctly"""
    runner = CliRunner()

    with mock.patch("tmr.cli.PomodoroTimer") as MockTimer:
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
        assert mock_run_timer.call_args[0][0].display_text == (
            "WORK:1/2        "
        )


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
        assert calls[0].args[0].display_text == "WORK:1/2        "
        assert calls[1].args[0].display_text == "SHORT_BREAK:1/2 "


def test_pomodoro_timer_run_timer():
    """Verify _run_timer implementation calls Timer"""
    config = PomodoroConfig(
        work_sec=0.1,
        break_sec=0.1,
        long_break_sec=0.1,
        cycles=1,
    )
    timer = PomodoroTimer(config)

    with mock.patch("tmr.pomodoro.Timer") as MockTimer:
        instance = MockTimer.return_value
        instance.main.return_value = True  # Quit

        # Call _run_timer directly
        title = TimerTitle("TEST", "white", 16)
        ret = timer._run_timer(title, 10.0)

        assert ret is True
        MockTimer.assert_called_once()
        args = MockTimer.call_args
        assert args[0][0] == title
        assert args[0][1] == 10.0
        assert args[1]["enable_next"] is True
        instance.main.assert_called_once()
