#
# (c) 2026 Yoichi Tanibayashi
#
import pytest
from unittest.mock import MagicMock, patch
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
