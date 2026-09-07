from pathlib import Path
from unittest import mock

import pytest
from click.testing import CliRunner

from tmr.cli import cli
from tmr.config import config_path
from tmr.view import TimerTitle


@pytest.fixture
def write_config(tmp_path, monkeypatch):
    """`XDG_CONFIG_HOME` を tmp に向けて、設定ファイルを書く関数を返す。"""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    def _write(text: str) -> Path:
        path = tmp_path / "tmr" / "config.toml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    return _write


@pytest.fixture
def mock_timer():
    """`Timer` を差し替える。呼ばれた引数を見るために使う。"""
    with mock.patch("tmr.cli.Timer") as MockTimer:
        MockTimer.return_value.main.return_value = False
        yield MockTimer


def test_config_path_xdg(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert config_path() == tmp_path / "tmr" / "config.toml"


def test_config_path_default(tmp_path, monkeypatch):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert config_path() == tmp_path / ".config" / "tmr" / "config.toml"


def test_no_file_uses_code_default(tmp_path, monkeypatch, mock_timer):
    """ファイルが無ければ、黙ってコードの既定値を使う。"""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    result = CliRunner().invoke(cli, ["timer", "1"])

    assert result.exit_code == 0
    assert mock_timer.call_args[0][0] == TimerTitle("Timer", "blue")


def test_config_gives_defaults(write_config, mock_timer):
    """設定ファイルの値が既定値になる。`minutes` も省略できる。"""
    write_config(
        '[timer]\nminutes = 7\ntitle = "Work"\ntitle-color = "green"\n'
    )

    result = CliRunner().invoke(cli, ["timer"])

    assert result.exit_code == 0
    assert mock_timer.call_args[0][0] == TimerTitle("Work", "green")
    assert mock_timer.call_args[0][1] == 7 * 60


def test_command_line_wins(write_config, mock_timer):
    """コマンドライン引数が設定ファイルより優先される。"""
    write_config('[timer]\nminutes = 7\ntitle = "Work"\n')

    result = CliRunner().invoke(cli, ["timer", "2", "--title", "CLI"])

    assert result.exit_code == 0
    assert mock_timer.call_args[0][0] == TimerTitle("CLI", "blue")
    assert mock_timer.call_args[0][1] == 2 * 60


def test_alias_gets_config(write_config, mock_timer):
    """別名（`t`）でも `[timer]` の設定が効く。"""
    write_config('[timer]\nminutes = 3\ntitle = "Work"\n')

    result = CliRunner().invoke(cli, ["t"])

    assert result.exit_code == 0
    assert mock_timer.call_args[0][1] == 3 * 60


def test_underscore_key(write_config, mock_timer):
    """キーはアンダースコアでも書ける。"""
    write_config('[timer]\nminutes = 1\ntitle_color = "red"\n')

    result = CliRunner().invoke(cli, ["timer"])

    assert result.exit_code == 0
    assert mock_timer.call_args[0][0] == TimerTitle("Timer", "red")


def test_pomodoro_config(write_config):
    """`[pomodoro]` も同じように効く。"""
    write_config("[pomodoro]\nwork-time = 1.0\ncycles = 2\n")

    with mock.patch("tmr.cli.PomodoroTimer") as MockPomodoro:
        MockPomodoro.return_value.run.return_value = False

        result = CliRunner().invoke(cli, ["pomodoro"])

    assert result.exit_code == 0
    config = MockPomodoro.call_args[0][0]
    assert config.work_sec == 1.0 * 60
    assert config.cycles == 2


def test_broken_toml(write_config):
    """TOML が壊れていたらエラーで終了する。"""
    write_config("[timer\n")

    result = CliRunner().invoke(cli, ["timer", "1"])

    assert result.exit_code != 0
    assert "config.toml" in result.output


def test_unknown_section(write_config):
    """知らないセクションはエラーで終了する。"""
    write_config("[tomato]\nx = 1\n")

    result = CliRunner().invoke(cli, ["timer", "1"])

    assert result.exit_code != 0
    assert "知らないセクション: [tomato]" in result.output


def test_unknown_key(write_config):
    """知らないキーはエラーで終了する。"""
    write_config('[timer]\ntitel = "x"\n')

    result = CliRunner().invoke(cli, ["timer", "1"])

    assert result.exit_code != 0
    assert "知らないキー: 'titel'" in result.output


def test_unknown_top_level_key(write_config):
    """先頭（セクションの外）の知らないキーもエラーで終了する。"""
    write_config("minutes = 5\n")

    result = CliRunner().invoke(cli, ["timer", "1"])

    assert result.exit_code != 0
    assert "知らないキー: 'minutes'" in result.output


def test_bad_type(write_config):
    """型が合わなければ click がエラーにする。"""
    write_config('[timer]\nalarm-count = "abc"\n')

    result = CliRunner().invoke(cli, ["timer", "1"])

    assert result.exit_code != 0
    assert "--alarm-count" in result.output
