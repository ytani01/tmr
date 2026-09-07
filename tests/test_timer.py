#
# (c) 2026 Yoichi Tanibayashi
#
from unittest.mock import MagicMock, patch

import pytest

from tmr.timer import Timer


@pytest.fixture
def mock_terminal():
    with patch("tmr.timer.Terminal") as mock:
        yield mock


@pytest.fixture
def mock_pbar():
    with patch("tmr.timer.ProgressBar") as mock:
        yield mock


@pytest.fixture
def mock_click():
    with patch("tmr.timer.click") as mock:
        yield mock


@pytest.fixture
def mock_time():
    with patch("tmr.timer.time") as mock:
        yield mock


@pytest.fixture
def timer(mock_terminal, mock_pbar, mock_click, mock_time):
    """
    Fixture for Timer with mocked dependencies.
    """
    # Set default values for terminal size to avoid comparison errors
    mock_terminal.return_value.width = 80
    mock_terminal.return_value.height = 24

    # Access fixtures to satisfy linters (as they are needed for patching)
    _ = (mock_pbar, mock_click, mock_time)

    return Timer()


def test_init_mocks(timer, mock_terminal, mock_pbar):
    """
    Verify that Timer is initialized with mocked dependencies.
    """
    # Check if term is an instance of the mock class (return_value of the class mock)
    assert timer.term == mock_terminal.return_value
    assert timer.pbar == mock_pbar.return_value


def test_initial_state(timer):
    """
    Verify the initial state of Timer.
    """
    assert timer.is_active is False
    assert timer.is_paused is False
    assert timer.alarm_active is False
    assert timer.quit_by_quitcmd is False


def test_fn_pause(timer):
    """
    Verify fn_pause toggles is_paused.
    """
    timer.fn_pause()
    assert timer.is_paused is True
    timer.fn_pause()
    assert timer.is_paused is False


def test_fn_quit(timer):
    """
    Verify fn_quit updates states correctly.
    """
    timer.is_active = True
    timer.is_paused = True
    timer.alarm_active = True

    timer.fn_quit()

    assert timer.is_active is False
    assert timer.is_paused is False
    assert timer.alarm_active is False
    assert timer.quit_by_quitcmd is True


def test_fn_forward(timer, mock_time):
    """
    Verify fn_forward advances time correctly.
    """
    mock_time.monotonic.return_value = 100.0
    timer.t_limit = 180.0
    timer.t_start = 100.0
    timer.t_elapsed = 0.0

    # 10秒進める -> t_start が 10秒前(90.0)になる
    timer.fn_forward(10.0)
    assert timer.t_start == 90.0
    assert timer.t_elapsed == 10.0

    # 限界を超えて進める
    timer.fn_forward(200.0)
    assert timer.t_start == 100.0 - 180.0  # t_cur - t_limit
    assert timer.t_elapsed == 180.0


def test_fn_backward(timer, mock_time):
    """
    Verify fn_backward moves time back correctly.
    """
    mock_time.monotonic.return_value = 100.0
    timer.t_limit = 180.0
    timer.t_start = 90.0
    timer.t_elapsed = 10.0

    # 5秒戻す -> t_start が 5秒後(95.0)になる
    timer.fn_backward(5.0)
    assert timer.t_start == 95.0
    assert timer.t_elapsed == 5.0

    # 限界(開始時)を超えて戻す
    timer.fn_backward(100.0)
    assert timer.t_start == 100.0  # t_cur
    assert timer.t_elapsed == 0.0


def test_responsive_layout(timer, mock_terminal):
    """
    Verify that columns are disabled when the terminal width is small.
    """
    # 広い幅: 全てのカラムが使われるはず
    timer.term.width = 200
    timer.display()
    assert all(col.use for col in timer.col.values())

    # 非常に狭い幅: 一部のカラムが disabled になるはず
    # 表示優先順 (低優先度から削除): date, time, elapsed, rate, limit, pbar, state, title, remain
    timer.term.width = 10
    timer.display()

    # 低優先度の date や time は False になっているはず
    assert timer.col["date"].use is False
    assert timer.col["time"].use is False

    # 超極小幅: 全て消えるか、!? が表示される
    timer.term.width = 1
    timer.display()
    assert not any(col.use for col in timer.col.values())


def test_rate_color(timer):
    """
    Verify that colors change based on the elapsed time rate.
    """
    timer.t_limit = 100.0

    # 0% - white
    timer.t_elapsed = 0.0
    timer.display()
    assert timer.col["remain"].color == "white"

    # 85% - yellow
    timer.t_elapsed = 85.0
    timer.display()
    assert timer.col["remain"].color == "yellow"

    # 96% - red
    timer.t_elapsed = 96.0
    timer.display()
    assert timer.col["remain"].color == "red"


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


def test_key_mapping(timer):
    """
    Verify that keys are mapped to the correct functions.
    """
    # Check some key mappings
    assert timer.key_map["P"] == timer.fn_pause
    assert timer.key_map[" "] == timer.fn_pause
    assert timer.key_map["Q"] == timer.fn_quit
    assert timer.key_map["KEY_ESCAPE"] == timer.fn_quit


def test_edge_cases_and_robustness(timer, mock_terminal, mock_click):
    """
    Verify behavior in edge cases like extremely small width and unknown keys.
    """
    # Extremely small width - display should print "!?"
    timer.term.width = 0
    timer.display()
    mock_click.secho.assert_called_with("\r\x1b[2K!?", blink=True, nl=False)

    # Unknown key - get_key_name should handle it gracefully
    mock_key = MagicMock()
    mock_key.name = None
    # Some control char
    setattr(mock_key, "__str__", MagicMock(return_value="\x01"))
    timer.term.inkey.return_value = mock_key
    assert timer.get_key_name() == "\x01"

    # Empty title
    timer.col["title"].value = ""
    timer.term.width = 80
    timer.display()
    # Should not crash and should work normally


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


def test_main_loop_simple(timer, mock_time, mock_terminal, mock_click):
    """
    Verify the main loop runs and terminates correctly.
    """
    # Mock monotonic to return sequence: start, loop1, loop2 (trigger limit)
    mock_time.monotonic.side_effect = [100.0, 101.0, 281.0, 281.0, 281.0]
    timer.t_limit = 180.0

    # Mock get_key_name to return nothing and then quit
    # (Though we'll terminate by time limit here)
    with patch.object(Timer, "get_key_name", side_effect=["", ""]):
        with patch.object(Timer, "ring_alarm", return_value=False):
            timer.main()

    assert timer.is_active is False
    assert timer.alarm_active is False


def test_ring_alarm_and_thread(timer, mock_click):
    """
    Verify ring_alarm starts a thread.
    """
    timer.alarm_active = True
    timer.alarm_params = (1, 0.01, 0.01)

    with patch("threading.Thread") as mock_thread:
        timer.ring_alarm()
        mock_thread.assert_called_once()

    # Test the thread function itself
    timer.alarm_active = True
    timer.thr_alarm(1, 0.001, 0.001)
    assert mock_click.echo.called  # Should call '\a'
    assert timer.alarm_active is False


def test_alarm_stop_by_key(timer, mock_terminal, mock_click, mock_time):
    """
    Verify alarm stops when a key is pressed.
    """
    timer.alarm_active = True

    # Mock time.monotonic to advance time
    # 1. init: 100.0
    # 2. main loop 1: 110.0 (elapsed 10.0 > limit 0.1) -> Limit Reached
    mock_time.monotonic.side_effect = [100.0, 110.0, 120.0]

    # Mock ring_alarm to return a dummy thread
    mock_thread = MagicMock()

    # Mock get_key_name:
    # 1. Main Loop 1: "" (No key)
    # 2. Alarm Loop 1: "KEY_ENTER" (Key pressed) -> Break

    with patch.object(Timer, "ring_alarm", return_value=mock_thread):
        with patch.object(
            Timer, "get_key_name", side_effect=["", "KEY_ENTER"]
        ):
            with patch("tmr.timer.Terminal.cbreak"):  # mock cbreak context
                timer.t_limit = 0.1

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


def test_display_hours(timer, mock_terminal):
    """
    Verify time string formatting for duration >= 1 hour.
    """
    # 1 hour + 1 minute + 1 second = 3661 seconds
    timer.t_limit = 3661.0
    timer.t_elapsed = 0.0

    # Run display to update columns
    timer.display()

    assert timer.col["limit"].value == "1h01m01s"

    # Check elapsed formatting as well
    timer.t_elapsed = 3661.0
    timer.display()
    assert timer.col["elapsed"].value == "1h01m01s"


def test_alarm_quit_by_quitcmd(timer, mock_terminal, mock_click, mock_time):
    """
    Verify that pressing 'q' during alarm sets quit_by_quitcmd = True.
    """
    timer.alarm_active = True

    # Advance time past limit
    mock_time.monotonic.side_effect = [100.0, 110.0, 120.0]

    mock_thread = MagicMock()

    # Main loop: "" (no key, timer expires)
    # Alarm loop: "Q" (quit key pressed)
    with patch.object(Timer, "ring_alarm", return_value=mock_thread):
        with patch.object(Timer, "get_key_name", side_effect=["", "Q"]):
            with patch("tmr.timer.Terminal.cbreak"):
                timer.t_limit = 0.1
                timer.main()

    assert timer.alarm_active is False
    assert timer.quit_by_quitcmd is True
    mock_thread.join.assert_called_once()


def test_display_pause_state(timer):
    """
    Verify [PAUSE] is shown when timer is paused.
    """
    timer.t_limit = 60.0
    timer.t_elapsed = 10.0

    # Not paused
    timer.is_paused = False
    timer.display()
    assert timer.col["state"].value == ""

    # Paused
    timer.is_paused = True
    timer.display()
    assert timer.col["state"].value == "[PAUSE]"
