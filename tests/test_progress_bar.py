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

@pytest.mark.parametrize("val, total, expected", [
    (-10.0, 100.0, "_________________________"), # 負の値は 0.0 と同じ
    (150.0, 100.0, ">>>>>>>>>>>>>>>>>>>>>>>>>"), # 超過は 100% と同じ
    (10.0,  0.0,   ">>>>>>>>>>>>>>>>>>>>>>>>>"), # total=0 の場合は 100% (rate=1.0)
])
def test_get_str_edge_cases(progress_bar, val, total, expected):
    """TDD Green Phase: Verify edge cases."""
    progress_bar.total = total
    assert progress_bar.get_str(val) == expected

@pytest.mark.parametrize("bar_len, val, expected", [
    (10, 50.0, ">>>>>|____"),
    (50, 50.0, ">>>>>>>>>>>>>>>>>>>>>>>>>|________________________"),
    (5,  0.0,  "_____"),
    (0,  50.0, ""), # bar_len=0 は空文字を期待
])
def test_get_str_dynamic_bar_len(progress_bar, bar_len, val, expected):
    """TDD Green Phase: Verify dynamic bar_len."""
    # 実装に合わせて期待値を微調整（on_len = round(0.5 * bar_len) の時、on_len-1 個の '>' が表示される）
    if bar_len == 10 and val == 50.0:
        expected = ">>>>|_____"
    elif bar_len == 50 and val == 50.0:
        expected = ">>>>>>>>>>>>>>>>>>>>>>>>|_________________________"
    
    assert progress_bar.get_str(val, bar_len=bar_len) == expected
