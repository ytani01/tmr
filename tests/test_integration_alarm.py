#
# (c) 2026 Yoichi Tanibayashi
#
import time
from unittest.mock import patch

from tmr.base_timer import BaseTimer


def test_alarm_thread_lifecycle():
    """
    Integration test to verify the alarm thread starts and can be stopped.
    This test uses short durations to avoid long waits.
    """
    # Use small alarm parameters
    alarm_params = (10, 0.01, 0.01)  # 10 times, total ~0.2s

    with patch("tmr.base_timer.click.echo") as mock_echo:
        timer = BaseTimer(alarm_params=alarm_params)
        timer.alarm_active = True

        # Start alarm
        thr = timer.ring_alarm()
        assert thr is not None
        assert thr.is_alive()

        # Give it a tiny bit of time to run at least one loop
        time.sleep(0.05)
        assert mock_echo.called

        # Stop alarm manually
        timer.alarm_active = False

        # Wait for thread to finish (should stop quickly due to flag check)
        thr.join(timeout=1.0)
        assert not thr.is_alive()


def test_alarm_thread_completes():
    """
    Verify the alarm thread completes naturally after count is reached.
    """
    alarm_params = (2, 0.01, 0.01)

    with patch("tmr.base_timer.click.echo") as mock_echo:
        timer = BaseTimer(alarm_params=alarm_params)
        timer.alarm_active = True

        thr = timer.ring_alarm()
        assert thr is not None

        thr.join(timeout=1.0)
        assert not thr.is_alive()
        assert timer.alarm_active is False
        # Expected calls: 2 * 2 (beep \a) = 4
        assert mock_echo.call_count >= 2
