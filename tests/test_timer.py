#
# (c) 2026 Yoichi Tanibayashi
#
from unittest.mock import MagicMock, patch

import pytest

from tmr.timer import AlarmParams, Timer
from tmr.view import TimerTitle


@pytest.fixture
def mock_terminal():
    with patch("tmr.timer.Terminal") as mock:
        yield mock


@pytest.fixture
def mock_view():
    with patch("tmr.timer.TimerView") as mock:
        yield mock


@pytest.fixture
def mock_click():
    with patch("tmr.timer.click") as mock:
        yield mock


@pytest.fixture
def mock_time():
    """tmr.timer の time (アラームの sleep)。"""
    with patch("tmr.timer.time") as mock:
        yield mock


@pytest.fixture
def mock_clock_time():
    """tmr.clock の time (経過時間の計算)。"""
    with patch("tmr.clock.time") as mock:
        yield mock


@pytest.fixture
def timer(mock_terminal, mock_view, mock_click, mock_time, mock_clock_time):
    """
    Fixture for Timer with mocked dependencies.
    """
    # Set default values for terminal size to avoid comparison errors
    mock_terminal.return_value.width = 80
    mock_terminal.return_value.height = 24

    # Access fixtures to satisfy linters (as they are needed for patching)
    _ = (mock_view, mock_click, mock_time, mock_clock_time)

    return Timer()


def test_init_mocks(timer, mock_terminal, mock_view):
    """
    Verify that Timer is initialized with mocked dependencies.
    """
    assert timer.term == mock_terminal.return_value
    assert timer.view == mock_view.return_value
    # Terminal は Timer が作り、View に渡す
    assert mock_view.call_args[0][0] == mock_terminal.return_value


def test_init_defaults(timer, mock_view):
    """
    Verify default title / alarm params.
    """
    # title は View に渡され、Timer 自身は持たない
    assert mock_view.call_args[0][2] == TimerTitle("Timer", "white")
    assert timer.alarm_params == AlarmParams(999, 0.5, 1.5)
    assert timer.clock.t_limit == Timer.DEF_LIMIT


def test_initial_state(timer):
    """
    Verify the initial state of Timer.
    """
    assert timer.is_active is False
    assert timer.clock.is_paused is False
    assert timer.alarm_active is False
    assert timer.quit_by_quitcmd is False


def test_fn_pause(timer):
    """
    Verify fn_pause toggles clock.is_paused.
    """
    timer.fn_pause()
    assert timer.clock.is_paused is True
    timer.fn_pause()
    assert timer.clock.is_paused is False


def test_fn_quit(timer):
    """
    Verify fn_quit updates states correctly.
    """
    timer.is_active = True
    timer.clock.is_paused = True
    timer.alarm_active = True

    timer.fn_quit()

    assert timer.is_active is False
    assert timer.clock.is_paused is False
    assert timer.alarm_active is False
    assert timer.quit_by_quitcmd is True


def test_fn_forward(timer, mock_clock_time):
    """
    Verify fn_forward delegates to clock.
    """
    mock_clock_time.monotonic.return_value = 100.0
    timer.clock.t_limit = 180.0
    timer.clock.t_start = 100.0
    timer.clock.elapsed = 0.0

    timer.fn_forward(10.0)
    assert timer.clock.t_start == 90.0
    assert timer.clock.elapsed == 10.0


def test_fn_backward(timer, mock_clock_time):
    """
    Verify fn_backward delegates to clock.
    """
    mock_clock_time.monotonic.return_value = 100.0
    timer.clock.t_limit = 180.0
    timer.clock.t_start = 90.0
    timer.clock.elapsed = 10.0

    timer.fn_backward(5.0)
    assert timer.clock.t_start == 95.0
    assert timer.clock.elapsed == 5.0


def test_get_key_name(timer, mock_terminal):
    """
    Verify get_key_name correctly identifies pressed keys.
    """
    # Mocking inkey result
    mock_key = MagicMock()
    mock_key.name = "KEY_ENTER"
    timer.term.inkey.return_value = mock_key

    assert timer.get_key_name() == "KEY_ENTER"

    # Character key
    mock_key.name = None
    # Use setattr to avoid lint errors with static analyzers
    setattr(mock_key, "__str__", MagicMock(return_value="p"))
    assert timer.get_key_name() == "P"

    # Timeout (no key)
    timer.term.inkey.return_value = None
    assert timer.get_key_name() == ""


def test_get_key_name_unknown(timer, mock_terminal):
    """
    Verify get_key_name handles a control char gracefully.
    """
    mock_key = MagicMock()
    mock_key.name = None
    # Some control char
    setattr(mock_key, "__str__", MagicMock(return_value="\x01"))
    timer.term.inkey.return_value = mock_key
    assert timer.get_key_name() == "\x01"


def test_key_mapping(timer):
    """
    Verify that keys are mapped to the correct functions.
    """
    # Check some key mappings
    assert timer.key_map["P"] == timer.fn_pause
    assert timer.key_map[" "] == timer.fn_pause
    assert timer.key_map["Q"] == timer.fn_quit
    assert timer.key_map["KEY_ESCAPE"] == timer.fn_quit


def test_keys_str(timer):
    """
    Verify keys_str formatting.
    """
    assert timer.keys_str(["P", " "]) == "[P], [SPACE]"
    assert timer.keys_str(["KEY_ENTER"]) == "[ENTER]"


def test_mk_cmd_str(timer):
    """
    Verify mk_cmd_str formatting.
    """
    cmd = timer.cmd[0]  # pause
    assert "Pause timer." in timer.mk_cmd_str(cmd)


def test_fn_help(timer, mock_click):
    """
    Verify fn_help prints command list.
    """
    timer.fn_help()
    # Should call echo multiple times
    assert mock_click.echo.called


def test_main_loop_simple(timer, mock_clock_time, mock_terminal, mock_click):
    """
    Verify the main loop runs and terminates correctly.
    """
    # Mock monotonic to return sequence: start, loop1, loop2 (trigger limit)
    mock_clock_time.monotonic.side_effect = [100.0, 101.0, 281.0]
    timer.clock.t_limit = 180.0

    # Mock get_key_name to return nothing and then quit
    # (Though we'll terminate by time limit here)
    with patch.object(Timer, "get_key_name", side_effect=["", ""]):
        with patch.object(Timer, "ring_alarm", return_value=False):
            timer.main()

    assert timer.is_active is False
    assert timer.alarm_active is False
    assert timer.clock.elapsed == 180.0


def test_main_loop_display(timer, mock_clock_time, mock_view):
    """
    Verify the main loop asks the view to display.
    """
    mock_clock_time.monotonic.side_effect = [100.0, 281.0]
    timer.clock.t_limit = 180.0

    with patch.object(Timer, "get_key_name", side_effect=[""]):
        with patch.object(Timer, "ring_alarm", return_value=False):
            timer.main()

    assert mock_view.return_value.display.called
    call = mock_view.return_value.display.call_args
    assert call[0][0] is timer.clock
    assert "is_active" in call[1]
    assert "alarm_active" in call[1]


def test_ring_alarm_and_thread(timer, mock_click):
    """
    Verify ring_alarm starts a thread.
    """
    timer.alarm_active = True
    timer.alarm_params = AlarmParams(1, 0.01, 0.01)

    with patch("threading.Thread") as mock_thread:
        timer.ring_alarm()
        mock_thread.assert_called_once()
        assert mock_thread.call_args[1]["args"] == (1, 0.01, 0.01)

    # Test the thread function itself
    timer.alarm_active = True
    timer.thr_alarm(1, 0.001, 0.001)
    assert mock_click.echo.called  # Should call '\a'
    assert timer.alarm_active is False


def test_ring_alarm_inactive(timer):
    """
    Verify ring_alarm does nothing when alarm is not active.
    """
    timer.alarm_active = False
    assert timer.ring_alarm() is None


def test_alarm_stop_by_key(timer, mock_terminal, mock_click, mock_clock_time):
    """
    Verify alarm stops when a key is pressed.
    """
    timer.alarm_active = True

    # Mock time.monotonic to advance time
    # 1. init: 100.0
    # 2. main loop 1: 110.0 (elapsed 10.0 > limit 0.1) -> Limit Reached
    mock_clock_time.monotonic.side_effect = [100.0, 110.0, 120.0]

    # Mock ring_alarm to return a dummy thread
    mock_thread = MagicMock()

    # Mock get_key_name:
    # 1. Main Loop 1: "" (No key)
    # 2. Alarm Loop 1: "KEY_ENTER" (Key pressed) -> Break

    with patch.object(Timer, "ring_alarm", return_value=mock_thread):
        with patch.object(
            Timer, "get_key_name", side_effect=["", "KEY_ENTER"]
        ):
            timer.clock.t_limit = 0.1

            # Run main
            timer.main()

    assert timer.alarm_active is False
    assert timer.quit_by_quitcmd is False
    mock_thread.join.assert_called_once()


def test_fn_next(timer):
    """
    Verify fn_next behavior with enable_next flag.
    """
    # Default: enable_next=False
    timer.is_active = True
    timer.fn_next()
    assert timer.is_active is True  # Should not change

    # Enable next
    timer.enable_next = True
    timer.fn_next()
    assert timer.is_active is False
    assert timer.quit_by_quitcmd is False


def test_alarm_quit_by_quitcmd(
    timer, mock_terminal, mock_click, mock_clock_time
):
    """
    Verify that pressing 'q' during alarm sets quit_by_quitcmd = True.
    """
    timer.alarm_active = True

    # Advance time past limit
    mock_clock_time.monotonic.side_effect = [100.0, 110.0, 120.0]

    mock_thread = MagicMock()

    # Main loop: "" (no key, timer expires)
    # Alarm loop: "Q" (quit key pressed)
    with patch.object(Timer, "ring_alarm", return_value=mock_thread):
        with patch.object(Timer, "get_key_name", side_effect=["", "Q"]):
            timer.clock.t_limit = 0.1
            timer.main()

    assert timer.alarm_active is False
    assert timer.quit_by_quitcmd is True
    mock_thread.join.assert_called_once()
