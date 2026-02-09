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
