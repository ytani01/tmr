#
# (c) 2026 Yoichi Tanibayashi
#
from unittest.mock import patch

import pytest

from tmr.clock import TimerClock


@pytest.fixture
def mock_time():
    with patch("tmr.clock.time") as mock:
        yield mock


@pytest.fixture
def clock(mock_time):
    """t_limit=180.0 の TimerClock。"""
    _ = mock_time
    return TimerClock(180.0)


def test_initial_state(clock):
    """初期状態。"""
    assert clock.t_limit == 180.0
    assert clock.t_start == 0.0
    assert clock.elapsed == 0.0
    assert clock.is_paused is False


def test_start(clock, mock_time):
    """start() で開始時刻を記録し、経過時間を 0 にする。"""
    clock.elapsed = 100.0
    clock.is_paused = True
    mock_time.monotonic.return_value = 500.0

    clock.start()

    assert clock.t_start == 500.0
    assert clock.elapsed == 0.0
    assert clock.is_paused is False


def test_tick(clock, mock_time):
    """tick() で経過時間が進み、t_limit で止まる。"""
    mock_time.monotonic.return_value = 100.0
    clock.start()

    mock_time.monotonic.return_value = 110.0
    clock.tick()
    assert clock.elapsed == 10.0

    # t_limit を超えない
    mock_time.monotonic.return_value = 400.0
    clock.tick()
    assert clock.elapsed == 180.0


def test_tick_paused(clock, mock_time):
    """ポーズ中は経過時間が止まり、t_start がずれる。"""
    mock_time.monotonic.return_value = 100.0
    clock.start()

    mock_time.monotonic.return_value = 110.0
    clock.tick()
    assert clock.elapsed == 10.0

    clock.toggle_pause()
    assert clock.is_paused is True

    mock_time.monotonic.return_value = 150.0
    clock.tick()
    assert clock.elapsed == 10.0  # 止まったまま
    assert clock.t_start == 140.0  # t_cur - elapsed

    # 再開後は、ポーズ中の分が経過に入らない
    clock.toggle_pause()
    mock_time.monotonic.return_value = 155.0
    clock.tick()
    assert clock.elapsed == 15.0


def test_forward(clock, mock_time):
    """早送り。"""
    mock_time.monotonic.return_value = 100.0
    clock.t_start = 100.0
    clock.elapsed = 0.0

    # 10秒進める -> t_start が 10秒前(90.0)になる
    clock.forward(10.0)
    assert clock.t_start == 90.0
    assert clock.elapsed == 10.0

    # 限界を超えて進める
    clock.forward(200.0)
    assert clock.t_start == 100.0 - 180.0  # t_cur - t_limit
    assert clock.elapsed == 180.0


def test_backward(clock, mock_time):
    """巻き戻し。"""
    mock_time.monotonic.return_value = 100.0
    clock.t_start = 90.0
    clock.elapsed = 10.0

    # 5秒戻す -> t_start が 5秒後(95.0)になる
    clock.backward(5.0)
    assert clock.t_start == 95.0
    assert clock.elapsed == 5.0

    # 限界(開始時)を超えて戻す
    clock.backward(100.0)
    assert clock.t_start == 100.0  # t_cur
    assert clock.elapsed == 0.0


def test_remain(clock):
    """残り時間。"""
    clock.elapsed = 0.0
    assert clock.remain == 180.0

    clock.elapsed = 30.0
    assert clock.remain == 150.0

    # 経過が limit を超えても負にならない
    clock.elapsed = 200.0
    assert clock.remain == 0


def test_rate(clock):
    """経過率 [%]。"""
    clock.elapsed = 0.0
    assert clock.rate == 0.0

    clock.elapsed = 90.0
    assert clock.rate == 50.0

    clock.elapsed = 180.0
    assert clock.rate == 100.0


def test_is_timeup(clock):
    """満了判定。"""
    clock.elapsed = 179.9
    assert clock.is_timeup is False

    clock.elapsed = 180.0
    assert clock.is_timeup is True

    clock.elapsed = 200.0
    assert clock.is_timeup is True
