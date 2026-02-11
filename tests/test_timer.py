from unittest import mock

from click.testing import CliRunner

from tmr.__main__ import timer


def test_timer_help():
    runner = CliRunner()
    result = runner.invoke(timer, ["--help"])
    assert result.exit_code == 0
    assert "Simple Timer" in result.output
    assert "--alarm-count" in result.output
    assert "--alarm-sec1" in result.output


def test_timer_exec():
    runner = CliRunner()
    with mock.patch("tmr.__main__.BaseTimer") as MockTimer:
        instance = MockTimer.return_value
        instance.main.return_value = False

        result = runner.invoke(timer, ["1"])  # 1 minute

        assert result.exit_code == 0

        # Verify BaseTimer initialization
        MockTimer.assert_called_once()
        args = MockTimer.call_args
        # args[0][0] is title ("Timer", "blue")
        assert args[0][0] == ("Timer", "blue")
        # args[0][1] is limit (1 * 60 = 60)
        assert args[0][1] == 60

        # Verify main called
        instance.main.assert_called_once()
