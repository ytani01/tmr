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

@pytest.mark.parametrize("val, expected", [
    (0.0,   "_________________________"),  # 現状 0.0 では風車が出ない仕様のよう
    (50.0,  ">>>>>>>>>>>|_____________"),
    (100.0, ">>>>>>>>>>>>>>>>>>>>>>>>>"),
])
def test_get_str_normal(progress_bar, val, expected):
    """TDD Green Phase: Verify normal progress values."""
    assert progress_bar.get_str(val) == expected
