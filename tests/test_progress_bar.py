#
# (c) 2026 Yoichi Tanibayashi
#
"""Tests for ProgressBar class."""

import pytest
from tmr.progress_bar import ProgressBar


def test_progress_bar_init():
    """Test initialization."""
    pbar = ProgressBar(total=100.0)
    assert pbar.total == 100.0
    assert pbar.val == 0.0


@pytest.mark.parametrize(
    "total, val, bar_len, expected_body",
    [
        (100.0, 0.0, 10, "__________"),
        (100.0, 50.0, 10, ">>>>>_____"),
        (100.0, 100.0, 10, ">>>>>>>>>>"),
        (0.0, 0.0, 10, ">>>>>>>>>>"),     # total=0 -> 100%
        (100.0, 150.0, 10, ">>>>>>>>>>"),   # val > total -> 100%
        (100.0, -10.0, 10, "__________"),   # val < 0 -> 0%
    ],
)
def test_progress_bar_get_str(total, val, bar_len, expected_body):
    """Test get_str method with various values."""
    pbar = ProgressBar(total=total, bar_length=bar_len)
    # ESQ_EL0 = \x1b[0K
    expected = f"\x1b[0K{expected_body}"
    assert pbar.get_str(val, stop=True) == expected


def test_progress_bar_custom_chars():
    """Test custom characters."""
    pbar = ProgressBar(total=100.0, bar_length=5, ch=("*", "."))
    # val=60% -> on_len=3. str_on="**", str_cur="*", str_off=".."
    assert pbar.get_str(60.0, stop=True) == "\x1b[0K***.."
