#
# (c) 2026 Yoichi Tanibayashi
#
from unittest.mock import patch

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

    
