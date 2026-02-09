#
# (c) 2026 Yoichi Tanibayashi
#
import pytest
from tmr.progress_bar import ProgressBar

@pytest.fixture
def progress_bar():
    return ProgressBar(total=100.0)

def test_progress_bar_instance(progress_bar):
    """Verify that the fixture creates a valid ProgressBar instance."""
    assert isinstance(progress_bar, ProgressBar)
    assert progress_bar.total == 100.0
