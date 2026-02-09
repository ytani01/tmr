#
# (c) 2026 Yoichi Tanibayashi
#
from unittest.mock import MagicMock, patch

import pytest

from tmr.base_timer import BaseTimer


@pytest.fixture
def mock_terminal():
    with patch("tmr.base_timer.Terminal") as mock:
        yield mock


@pytest.fixture
def mock_pbar():
    with patch("tmr.base_timer.ProgressBar") as mock:
        yield mock


@pytest.fixture
def mock_click():
    with patch("tmr.base_timer.click") as mock:
        yield mock


@pytest.fixture
def mock_time():
    with patch("tmr.base_timer.time") as mock:
        yield mock


@pytest.fixture
def base_timer(mock_terminal, mock_pbar, mock_click, mock_time):
    """
    Fixture for BaseTimer with mocked dependencies.
    """
    # Set default values for terminal size to avoid comparison errors
    mock_terminal.return_value.width = 80
    mock_terminal.return_value.height = 24
    return BaseTimer()


def test_init_mocks(base_timer, mock_terminal, mock_pbar):
    """
    Verify that BaseTimer is initialized with mocked dependencies.
    """
    # Check if term is an instance of the mock class (return_value of the class mock)
    assert base_timer.term == mock_terminal.return_value
    assert base_timer.pbar == mock_pbar.return_value


def test_initial_state(base_timer):
    """
    Verify the initial state of BaseTimer.
    """
    assert base_timer.is_active is False
    assert base_timer.is_paused is False
    assert base_timer.alarm_active is False
    assert base_timer.cmd_quit is False


def test_fn_pause(base_timer):
    """
    Verify fn_pause toggles is_paused.
    """
    base_timer.fn_pause()
    assert base_timer.is_paused is True
    base_timer.fn_pause()
    assert base_timer.is_paused is False


def test_fn_quit(base_timer):
    """
    Verify fn_quit updates states correctly.
    """
    base_timer.is_active = True
    base_timer.is_paused = True
    base_timer.alarm_active = True

    base_timer.fn_quit()

    assert base_timer.is_active is False
    assert base_timer.is_paused is False
    assert base_timer.alarm_active is False
    assert base_timer.cmd_quit is True


def test_fn_forward(base_timer, mock_time):
    """
    Verify fn_forward advances time correctly.
    """
    mock_time.monotonic.return_value = 100.0
    base_timer.t_limit = 180.0
    base_timer.t_start = 100.0
    base_timer.t_elapsed = 0.0

    # 10秒進める -> t_start が 10秒前(90.0)になる
    base_timer.fn_forward(10.0)
    assert base_timer.t_start == 90.0
    assert base_timer.t_elapsed == 10.0

    # 限界を超えて進める
    base_timer.fn_forward(200.0)
    assert base_timer.t_start == 100.0 - 180.0  # t_cur - t_limit
    assert base_timer.t_elapsed == 180.0


def test_fn_backward(base_timer, mock_time):
    """
    Verify fn_backward moves time back correctly.
    """
    mock_time.monotonic.return_value = 100.0
    base_timer.t_limit = 180.0
    base_timer.t_start = 90.0
    base_timer.t_elapsed = 10.0

    # 5秒戻す -> t_start が 5秒後(95.0)になる
    base_timer.fn_backward(5.0)
    assert base_timer.t_start == 95.0
    assert base_timer.t_elapsed == 5.0

    # 限界(開始時)を超えて戻す
    base_timer.fn_backward(100.0)
    assert base_timer.t_start == 100.0 # t_cur
    assert base_timer.t_elapsed == 0.0

def test_responsive_layout(base_timer, mock_terminal):
    """
    Verify that columns are disabled when the terminal width is small.
    """
    # 広い幅: 全てのカラムが使われるはず
    base_timer.term.width = 200
    base_timer.display()
    assert all(col.use for col in base_timer.col.values())

    # 非常に狭い幅: 一部のカラムが disabled になるはず
    # 表示優先順 (低優先度から削除): date, time, elapsed, rate, limit, pbar, state, title, remain
    base_timer.term.width = 10
    base_timer.display()
    
    # 低優先度の date や time は False になっているはず
    assert base_timer.col["date"].use is False
    assert base_timer.col["time"].use is False
    
    # 超極小幅: 全て消えるか、!? が表示される
    base_timer.term.width = 1
    base_timer.display()
    assert not any(col.use for col in base_timer.col.values())

def test_rate_color(base_timer):
    """
    Verify that colors change based on the elapsed time rate.
    """
    base_timer.t_limit = 100.0
    
    # 0% - white
    base_timer.t_elapsed = 0.0
    base_timer.display()
    assert base_timer.col["remain"].color == "white"
    
    # 85% - yellow
    base_timer.t_elapsed = 85.0
    base_timer.display()
    assert base_timer.col["remain"].color == "yellow"
    
    # 96% - red
    base_timer.t_elapsed = 96.0
    base_timer.display()
    assert base_timer.col["remain"].color == "red"

def test_get_key_name(base_timer, mock_terminal):
    """
    Verify get_key_name correctly identifies pressed keys.
    """
    # Mocking inkey result
    mock_key = MagicMock()
    mock_key.name = "KEY_ENTER"
    base_timer.term.inkey.return_value = mock_key
    
    assert base_timer.get_key_name() == "KEY_ENTER"
    
    # Character key
    mock_key.name = None
    # Use setattr to avoid lint errors with static analyzers
    setattr(mock_key, "__str__", MagicMock(return_value="p"))
    assert base_timer.get_key_name() == "p"
    
    # Timeout (no key)
    base_timer.term.inkey.return_value = None
    assert base_timer.get_key_name() == ""

def test_key_mapping(base_timer):
    """
    Verify that keys are mapped to the correct functions.
    """
    # Check some key mappings
    assert base_timer.key_map["p"] == base_timer.fn_pause
    assert base_timer.key_map[" "] == base_timer.fn_pause
    assert base_timer.key_map["q"] == base_timer.fn_quit
    assert base_timer.key_map["KEY_ESCAPE"] == base_timer.fn_quit

def test_edge_cases_and_robustness(base_timer, mock_terminal, mock_click):
    """
    Verify behavior in edge cases like extremely small width and unknown keys.
    """
    # Extremely small width - display should print "!?"
    base_timer.term.width = 0
    base_timer.display()
    mock_click.secho.assert_called_with("\r\x1b[2K!?", blink=True, nl=False)
    
    # Unknown key - get_key_name should handle it gracefully
    mock_key = MagicMock()
    mock_key.name = None
    setattr(mock_key, "__str__", MagicMock(return_value="\x01")) # Some control char
    base_timer.term.inkey.return_value = mock_key
    assert base_timer.get_key_name() == "\x01"
    
    # Empty title
    base_timer.col["title"].value = ""
    base_timer.term.width = 80
    base_timer.display()
    # Should not crash and should work normally

def test_keys_str(base_timer):
    """
    Verify keys_str formatting.
    """
    assert base_timer.keys_str(["p", " "]) == "[p], [SPACE]"
    assert base_timer.keys_str(["KEY_ENTER"]) == "[ENTER]"

def test_mk_cmd_str(base_timer):
    """
    Verify mk_cmd_str formatting.
    """
    cmd = base_timer.cmd[0] # pause
    assert "Pause timer." in base_timer.mk_cmd_str(cmd)

def test_fn_help(base_timer, mock_click):
    """
    Verify fn_help prints command list.
    """
    base_timer.fn_help()
    # Should call echo multiple times
    assert mock_click.echo.called

def test_main_loop_simple(base_timer, mock_time, mock_terminal, mock_click):
    """
    Verify the main loop runs and terminates correctly.
    """
    # Mock monotonic to return sequence: start, loop1, loop2 (trigger limit)
    mock_time.monotonic.side_effect = [100.0, 101.0, 281.0, 281.0, 281.0]
    base_timer.t_limit = 180.0
    
    # Mock get_key_name to return nothing and then quit
    # (Though we'll terminate by time limit here)
    with patch.object(BaseTimer, "get_key_name", side_effect=["", ""]):
        with patch.object(BaseTimer, "ring_alarm", return_value=False):
            base_timer.main()
    
    assert base_timer.is_active is False
    assert base_timer.alarm_active is True

def test_ring_alarm_and_thread(base_timer, mock_click):
    """
    Verify ring_alarm starts a thread.
    """
    base_timer.alarm_active = True
    base_timer.alarm_params = (1, 0.01, 0.01)
    
    with patch("threading.Thread") as mock_thread:
        base_timer.ring_alarm()
        mock_thread.assert_called_once()
        
    # Test the thread function itself
    base_timer.alarm_active = True
    base_timer.thr_alarm(1, 0.001, 0.001)
    assert mock_click.echo.called # Should call '\a'
    assert base_timer.alarm_active is False

    
