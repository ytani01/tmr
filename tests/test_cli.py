from unittest import mock

import pytest
from click.testing import CliRunner

from tmr.cli import pomodoro, timer
from tmr.timefmt import SEC_DAY
from tmr.view import TimerTitle


def test_timer_help():
    runner = CliRunner()
    result = runner.invoke(timer, ["--help"])
    assert result.exit_code == 0
    assert "Simple Timer" in result.output
    assert "--alarm-count" in result.output
    assert "--alarm-sec1" in result.output


def test_timer_exec():
    runner = CliRunner()
    with mock.patch("tmr.cli.Timer") as MockTimer:
        instance = MockTimer.return_value
        instance.main.return_value = False

        result = runner.invoke(timer, ["1"])  # 1 minute

        assert result.exit_code == 0

        # Verify Timer initialization
        MockTimer.assert_called_once()
        args = MockTimer.call_args
        # args[0][0] is title
        assert args[0][0] == TimerTitle("Timer", "blue")
        # args[0][1] is limit (1 * 60 = 60)
        assert args[0][1] == 60

        # Verify main called
        instance.main.assert_called_once()


@pytest.mark.parametrize("minutes", ["0", "-1"])
def test_timer_invalid_minutes_rejected(minutes):
    """0 / 負の分は click の usage error になる。"""
    runner = CliRunner()
    result = runner.invoke(timer, ["--", minutes])

    assert result.exit_code == 2
    assert "is not in the range" in result.output


@pytest.mark.parametrize("cycles", ["0", "-1"])
def test_pomodoro_invalid_cycles_rejected(cycles):
    """cycles=0 / 負値は click の usage error になる。"""
    runner = CliRunner()
    result = runner.invoke(pomodoro, ["--cycles", cycles])

    assert result.exit_code == 2
    assert "is not in the range" in result.output


@pytest.mark.parametrize("work_time", ["0", "-1"])
def test_pomodoro_invalid_work_time_rejected(work_time):
    """work-time=0 / 負値は click の usage error になる。"""
    runner = CliRunner()
    result = runner.invoke(pomodoro, ["--work-time", work_time])

    assert result.exit_code == 2
    assert "is not in the range" in result.output


@pytest.mark.parametrize(
    "option,value",
    [
        ("--work-time", "nan"),
        ("--work-time", "inf"),
        ("--break-time", "nan"),
        ("--long-break-time", "inf"),
    ],
)
def test_pomodoro_non_finite_rejected(option, value):
    """nan / inf は usage error になる（FloatRange の後段で弾く）。"""
    runner = CliRunner()
    result = runner.invoke(pomodoro, [option, value])

    assert result.exit_code == 2
    assert "must be finite" in result.output


def test_timer_alarm_count_negative_rejected():
    """--alarm-count が負値なら usage error になる。"""
    runner = CliRunner()
    result = runner.invoke(timer, ["1", "--alarm-count", "-1"])

    assert result.exit_code == 2
    assert "is not in the range" in result.output


@pytest.mark.parametrize("option", ["--alarm-sec1", "--alarm-sec2"])
def test_timer_alarm_sec_negative_rejected(option):
    """--alarm-sec1 / --alarm-sec2 が負値なら usage error になる。"""
    runner = CliRunner()
    result = runner.invoke(timer, ["1", option, "-1"])

    assert result.exit_code == 2
    assert "is not in the range" in result.output


def test_timer_alarm_sec1_nan_rejected():
    """--alarm-sec1 が nan なら usage error になる。"""
    runner = CliRunner()
    result = runner.invoke(timer, ["1", "--alarm-sec1", "nan"])

    assert result.exit_code == 2
    assert "must be finite" in result.output


def test_timer_alarm_sec2_inf_rejected():
    """--alarm-sec2 が inf なら usage error になる（上限超え）。"""
    runner = CliRunner()
    result = runner.invoke(timer, ["1", "--alarm-sec2", "inf"])

    assert result.exit_code == 2
    assert "is not in the range" in result.output


def test_timer_alarm_zero_allowed():
    """count=0・sec1=0・sec2=0 は通る（鳴らさない／間を空けない設定）。"""
    runner = CliRunner()
    with mock.patch("tmr.cli.Timer") as MockTimer:
        instance = MockTimer.return_value
        instance.main.return_value = False

        result = runner.invoke(
            timer,
            [
                "1",
                "--alarm-count",
                "0",
                "--alarm-sec1",
                "0",
                "--alarm-sec2",
                "0",
            ],
        )

        assert result.exit_code == 0
        instance.main.assert_called_once()

        # 境界の向きを取り違えていないか、渡った AlarmParams を確かめる
        args = MockTimer.call_args
        alarm_params = args[0][2]
        assert alarm_params.count == 0
        assert alarm_params.sec1 == 0.0
        assert alarm_params.sec2 == 0.0


@pytest.mark.parametrize("option", ["--alarm-sec1", "--alarm-sec2"])
def test_timer_alarm_sec_too_large_rejected(option):
    """アラームの間隔が上限（1 日）を超えると usage error になる。"""
    runner = CliRunner()
    result = runner.invoke(timer, ["1", option, "1e18"])

    assert result.exit_code == 2
    assert "is not in the range" in result.output


@pytest.mark.parametrize("option", ["--alarm-sec1", "--alarm-sec2"])
def test_timer_alarm_sec_max_allowed(option):
    """アラームの間隔は上限（1 日 = 86400 秒）ちょうどなら通る。"""
    runner = CliRunner()
    with mock.patch("tmr.cli.Timer") as MockTimer:
        instance = MockTimer.return_value
        instance.main.return_value = False

        result = runner.invoke(timer, ["1", option, str(SEC_DAY)])

        assert result.exit_code == 0
        instance.main.assert_called_once()
