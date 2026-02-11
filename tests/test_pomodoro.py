from click.testing import CliRunner
from tmr.__main__ import pomodoro

def test_pomodoro_args():
    runner = CliRunner()
    result = runner.invoke(pomodoro, ['--help'])
    assert result.exit_code == 0
    assert "pomodoro" in result.output
    # check default options
    assert "--work-time" in result.output
    assert "--break-time" in result.output
    assert "--long-break-time" in result.output
    assert "--cycles" in result.output
