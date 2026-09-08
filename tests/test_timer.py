#
# (c) 2026 Yoichi Tanibayashi
#
import signal
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from tmr.timer import MAX_ALARM_SEC, AlarmParams, Timer
from tmr.view import TimerTitle


@pytest.mark.parametrize(
    "count,sec1,sec2",
    [
        (-1, 0.5, 1.5),
        (0, -1, 1.5),
        (0, 0.5, -1),
        (0, float("nan"), 1.5),
        (0, 0.5, float("inf")),
    ],
)
def test_alarm_params_invalid_raises(count, sec1, sec2):
    """count / sec1 / sec2 が不正なら ValueError。"""
    with pytest.raises(ValueError):
        AlarmParams(count, sec1, sec2)


def test_alarm_params_zero_allowed():
    """count=0・sec=0 は「鳴らさない／間を空けない」として許す。"""
    params = AlarmParams(0, 0.0, 0.0)
    assert params.count == 0
    assert params.sec1 == 0.0
    assert params.sec2 == 0.0


@pytest.mark.parametrize("field", ["sec1", "sec2"])
def test_alarm_params_sec_too_large_raises(field):
    """sec1 / sec2 が上限（1 日）を超えると ValueError。"""
    sec1 = MAX_ALARM_SEC + 1 if field == "sec1" else 0.5
    sec2 = MAX_ALARM_SEC + 1 if field == "sec2" else 1.5

    with pytest.raises(ValueError):
        AlarmParams(count=0, sec1=sec1, sec2=sec2)


@pytest.mark.parametrize("field", ["sec1", "sec2"])
def test_alarm_params_sec_max_allowed(field):
    """sec1 / sec2 は上限（1 日）ちょうどなら通る。"""
    sec1 = MAX_ALARM_SEC if field == "sec1" else 0.5
    sec2 = MAX_ALARM_SEC if field == "sec2" else 1.5

    params = AlarmParams(count=0, sec1=sec1, sec2=sec2)
    assert getattr(params, field) == MAX_ALARM_SEC


@pytest.mark.parametrize("cmd", ["", " ", "\t"])
def test_alarm_params_empty_cmd_raises(cmd):
    """cmd が空文字・空白のみなら ValueError。"""
    with pytest.raises(ValueError):
        AlarmParams(1, 0.5, 1.5, cmd)


def test_alarm_params_cmd_none_allowed():
    """cmd=None（既定）は従来どおりビープ。"""
    params = AlarmParams(1, 0.5, 1.5)
    assert params.cmd is None


def test_alarm_params_cmd_allowed():
    """cmd に文字列を指定できる。"""
    params = AlarmParams(1, 0.5, 1.5, "echo hello")
    assert params.cmd == "echo hello"


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
def mock_subprocess():
    """tmr.timer の subprocess (アラームのコマンド実行)。"""
    with patch("tmr.timer.subprocess") as mock:
        proc = mock.Popen.return_value
        proc.communicate.return_value = ("", "")
        proc.returncode = 0
        proc.poll.return_value = 0  # 既に終わっている
        proc.pid = -1  # 実在しない（撃ってしまっても当たらない値）
        yield mock


@pytest.fixture
def mock_killpg():
    """tmr.timer の os.killpg (アラームのコマンドを止める)。"""
    with patch("tmr.timer.os.killpg") as mock:
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
    assert mock_view.call_args[0][1] == TimerTitle("Timer", "white")
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
        assert mock_thread.call_args[1]["args"] == (
            AlarmParams(1, 0.01, 0.01),
        )

    # Test the thread function itself
    timer.alarm_active = True
    timer.thr_alarm(AlarmParams(1, 0.001, 0.001))
    assert mock_click.echo.called  # Should call '\a'
    assert timer.alarm_active is False


def test_ring_alarm_inactive(timer):
    """
    Verify ring_alarm does nothing when alarm is not active.
    """
    timer.alarm_active = False
    assert timer.ring_alarm() is None


def test_thr_alarm_cmd(timer, mock_click, mock_subprocess):
    """cmd 指定時は、コマンドを 1 回だけ実行し、ビープを出さない。"""
    timer.alarm_active = True
    timer.thr_alarm(AlarmParams(3, 0.001, 0.001, "echo hello"))

    # 端末を取り合わないよう、stdin は捨て、出力は取り込む
    mock_subprocess.Popen.assert_called_once_with(
        "echo hello",
        shell=True,
        stdin=mock_subprocess.DEVNULL,
        stdout=mock_subprocess.PIPE,
        stderr=mock_subprocess.PIPE,
        text=True,
        errors="replace",
        start_new_session=True,
    )
    mock_subprocess.Popen.return_value.communicate.assert_called_once()
    assert not mock_click.echo.called
    # キー入力を待つため、alarm_active は False にしない
    assert timer.alarm_active is True


def test_thr_alarm_cmd_nonzero(timer, mock_click, mock_subprocess):
    """コマンドが非ゼロ終了しても、ビープにフォールバックしない。"""
    mock_subprocess.Popen.return_value.returncode = 1

    timer.alarm_active = True
    timer.thr_alarm(AlarmParams(3, 0.001, 0.001, "false"))

    mock_subprocess.Popen.assert_called_once()
    assert not mock_click.echo.called
    assert timer.alarm_active is True


def test_thr_alarm_cmd_oserror(timer, mock_click, mock_subprocess):
    """コマンドの実行に失敗しても例外を投げない。"""
    mock_subprocess.Popen.side_effect = OSError("no such command")

    timer.alarm_active = True
    timer.thr_alarm(AlarmParams(3, 0.001, 0.001, "no_such_command"))

    mock_subprocess.Popen.assert_called_once()
    assert not mock_click.echo.called
    assert timer.alarm_active is True
    assert timer.alarm_proc is None


def test_thr_alarm_cmd_output_to_log(timer, mock_click, mock_subprocess):
    """コマンドの出力は画面に出さず、ログに回す（長さは切り詰める）。"""
    proc = mock_subprocess.Popen.return_value
    proc.communicate.return_value = ("hello\n", "x" * (Timer.LOG_MAX_LEN * 2))

    with patch.object(Timer, "_Timer__log") as mock_log:
        timer.thr_alarm(AlarmParams(1, 0.001, 0.001, "echo hello"))

    logged = [
        call.args[0]
        for call in mock_log.debug.call_args_list
        if call.args and isinstance(call.args[0], str)
    ]
    assert "stdout: hello" in logged
    assert f"stderr: {'x' * Timer.LOG_MAX_LEN}" in logged
    assert not mock_click.echo.called


def test_thr_alarm_cmd_empty_output_not_logged(
    timer, mock_click, mock_subprocess
):
    """出力が無ければ、そのログは出さない。"""
    mock_subprocess.Popen.return_value.communicate.return_value = ("", " \n")

    with patch.object(Timer, "_Timer__log") as mock_log:
        timer.thr_alarm(AlarmParams(1, 0.001, 0.001, "true"))

    logged = [
        call.args[0]
        for call in mock_log.debug.call_args_list
        if call.args and isinstance(call.args[0], str)
    ]
    assert not [
        msg for msg in logged if msg.startswith(("stdout:", "stderr:"))
    ]


def test_main_with_alarm_cmd_failure(
    timer, mock_click, mock_clock_time, mock_subprocess, mock_killpg
):
    """コマンドが失敗しても、キー入力でアラームを抜けて終了する。"""
    mock_subprocess.Popen.side_effect = OSError("no such command")

    timer.alarm_params = AlarmParams(1, 0.001, 0.001, "no_such_command")
    mock_clock_time.monotonic.side_effect = [100.0, 110.0, 120.0]

    with patch.object(Timer, "get_key_name", side_effect=["", "KEY_ENTER"]):
        timer.clock.t_limit = 0.1
        assert timer.main() is False

    assert timer.alarm_active is False
    mock_subprocess.Popen.assert_called_once()
    # 起動に失敗したのだから、シグナルを送る相手も居ない
    mock_killpg.assert_not_called()


def test_main_quit_with_alarm_cmd(
    timer, mock_click, mock_clock_time, mock_subprocess, mock_killpg
):
    """cmd 経路でも [Q] なら main() は True を返す。

    ポモドーロのフェーズ制御は、この戻り値だけで決まる。
    """
    timer.alarm_params = AlarmParams(1, 0.001, 0.001, "echo hello")
    mock_clock_time.monotonic.side_effect = [100.0, 110.0, 120.0]

    with patch.object(Timer, "get_key_name", side_effect=["", "Q"]):
        timer.clock.t_limit = 0.1
        assert timer.main() is True

    assert timer.alarm_active is False
    assert timer.quit_by_quitcmd is True
    mock_subprocess.Popen.assert_called_once()
    # 自然に終わったコマンドにシグナルは送らない
    mock_killpg.assert_not_called()


def _running_proc(mock_subprocess, stop_event):
    """終わらないコマンドの proc モックを作る。

    stop_event がセットされるまで communicate() が返らない。
    """
    proc = mock_subprocess.Popen.return_value
    proc.poll.return_value = None  # 実行中

    def fake_communicate():
        assert stop_event.wait(timeout=5.0)
        return ("", "")

    proc.communicate.side_effect = fake_communicate
    return proc


def test_stop_alarm_cmd_sigterm(
    timer, mock_click, mock_subprocess, mock_killpg
):
    """実行中のコマンドは SIGTERM で止める。"""
    stop_event = threading.Event()
    proc = _running_proc(mock_subprocess, stop_event)
    mock_killpg.side_effect = lambda pid, sig: stop_event.set()

    timer.alarm_params = AlarmParams(1, 0.001, 0.001, "sleep 5")
    timer.alarm_active = True
    thr = timer.ring_alarm()
    assert thr is not None

    assert timer.stop_alarm_cmd(thr) is True
    # シェルの子（sleep）ごと落とすため、プロセスグループに送る
    mock_killpg.assert_called_once_with(proc.pid, signal.SIGTERM)
    assert not thr.is_alive()
    assert timer.alarm_cmd_stopped is True


def test_stop_alarm_cmd_sigkill(
    timer, mock_click, mock_subprocess, mock_killpg
):
    """SIGTERM で止まらなければ SIGKILL を送る。"""
    stop_event = threading.Event()
    proc = _running_proc(mock_subprocess, stop_event)

    def fake_killpg(pid, sig):
        if sig == signal.SIGKILL:
            stop_event.set()

    mock_killpg.side_effect = fake_killpg

    timer.ALARM_STOP_SEC = 0.05  # 待ち時間を詰める
    timer.alarm_params = AlarmParams(1, 0.001, 0.001, "sleep 5")
    timer.alarm_active = True
    thr = timer.ring_alarm()
    assert thr is not None

    assert timer.stop_alarm_cmd(thr) is True
    assert mock_killpg.call_args_list == [
        ((proc.pid, signal.SIGTERM),),
        ((proc.pid, signal.SIGKILL),),
    ]
    assert not thr.is_alive()


def test_stop_alarm_cmd_not_stopped(
    timer, mock_click, mock_subprocess, mock_killpg
):
    """SIGKILL でも止まらなければ False を返す（join で固まらない）。"""
    stop_event = threading.Event()
    _running_proc(mock_subprocess, stop_event)

    timer.ALARM_STOP_SEC = 0.05
    timer.alarm_params = AlarmParams(1, 0.001, 0.001, "sleep 5")
    timer.alarm_active = True
    thr = timer.ring_alarm()
    assert thr is not None

    assert timer.stop_alarm_cmd(thr) is False
    assert mock_killpg.call_count == 2

    stop_event.set()  # 後始末
    thr.join(timeout=5.0)


def test_stop_alarm_cmd_already_gone(
    timer, mock_click, mock_subprocess, mock_killpg
):
    """既に居ないプロセスへのシグナルは、失敗にしない。"""
    stop_event = threading.Event()
    _running_proc(mock_subprocess, stop_event)
    mock_killpg.side_effect = ProcessLookupError()

    timer.ALARM_STOP_SEC = 0.05
    timer.alarm_params = AlarmParams(1, 0.001, 0.001, "sleep 5")
    timer.alarm_active = True
    thr = timer.ring_alarm()
    assert thr is not None

    assert timer.stop_alarm_cmd(thr) is False  # スレッドは終わっていない
    assert mock_killpg.call_count == 2

    stop_event.set()
    thr.join(timeout=5.0)


def test_stop_alarm_cmd_oserror(
    timer, mock_click, mock_subprocess, mock_killpg
):
    """シグナルを送れなければ False（join せずに進む）。"""
    stop_event = threading.Event()
    _running_proc(mock_subprocess, stop_event)
    mock_killpg.side_effect = PermissionError()

    timer.alarm_params = AlarmParams(1, 0.001, 0.001, "sleep 5")
    timer.alarm_active = True
    thr = timer.ring_alarm()
    assert thr is not None

    assert timer.stop_alarm_cmd(thr) is False
    mock_killpg.assert_called_once()

    stop_event.set()
    thr.join(timeout=5.0)


def test_stop_alarm_cmd_waits_for_popen(
    timer, mock_click, mock_subprocess, mock_killpg
):
    """スレッドが起動し終える前に押されても、止めそこねない。

    Popen を作る前にキーを押されると alarm_proc がまだ None で、
    「止める相手が居ない」と判断して join() で固まってしまう。
    """
    stop_event = threading.Event()
    proc = _running_proc(mock_subprocess, stop_event)
    mock_killpg.side_effect = lambda pid, sig: stop_event.set()

    def slow_popen(*_args, **_kwargs):
        time.sleep(0.2)  # 起動に時間がかかる状況
        return proc

    mock_subprocess.Popen.side_effect = slow_popen

    timer.alarm_params = AlarmParams(1, 0.001, 0.001, "sleep 5")
    timer.alarm_active = True
    thr = timer.ring_alarm()
    assert thr is not None

    # Popen ができる前に止めにいく
    assert timer.alarm_proc is None
    assert timer.stop_alarm_cmd(thr) is True

    mock_killpg.assert_called_once_with(proc.pid, signal.SIGTERM)
    assert not thr.is_alive()


def test_main_resets_alarm_cmd_state(
    timer, mock_click, mock_clock_time, mock_subprocess, mock_killpg
):
    """同じ Timer で 2 回目を回しても、コマンドを止められる。

    ライブラリとして直接使う経路のため（CLI は毎回作り直す）。
    """
    timer.alarm_params = AlarmParams(1, 0.001, 0.001, "sleep 5")

    # 1 回目: コマンドは自然に終わったことにする
    mock_clock_time.monotonic.side_effect = [100.0, 110.0, 120.0]
    with patch.object(Timer, "get_key_name", side_effect=["", "KEY_ENTER"]):
        timer.clock.t_limit = 0.1
        assert timer.main() is False

    assert timer.alarm_proc is not None
    assert timer.alarm_proc_ready.is_set()

    # 2 回目: 終わらないコマンドでも、キーを押せば止まる
    stop_event = threading.Event()
    proc = _running_proc(mock_subprocess, stop_event)
    mock_killpg.side_effect = lambda pid, sig: stop_event.set()

    mock_clock_time.monotonic.side_effect = [200.0, 210.0, 220.0]
    with patch.object(Timer, "get_key_name", side_effect=["", "Q"]):
        timer.clock.t_limit = 0.1
        assert timer.main() is True

    mock_killpg.assert_called_once_with(proc.pid, signal.SIGTERM)
    assert stop_event.is_set()


def test_main_keyboard_interrupt_stops_alarm_cmd(
    timer, mock_click, mock_clock_time, mock_subprocess, mock_killpg
):
    """Ctrl-C で抜けるときも、コマンドを止めてから送出し直す。

    子は別セッションにいるので、端末の SIGINT は届かない。
    """
    stop_event = threading.Event()
    proc = _running_proc(mock_subprocess, stop_event)
    mock_killpg.side_effect = lambda pid, sig: stop_event.set()

    timer.alarm_params = AlarmParams(1, 0.001, 0.001, "sleep 5")
    mock_clock_time.monotonic.side_effect = [100.0, 110.0, 120.0]

    with patch.object(
        Timer, "get_key_name", side_effect=["", KeyboardInterrupt()]
    ):
        timer.clock.t_limit = 0.1
        with pytest.raises(KeyboardInterrupt):
            timer.main()

    mock_killpg.assert_called_once_with(proc.pid, signal.SIGTERM)
    assert stop_event.is_set()


def test_ring_alarm_blocks_sigint_for_thread(timer, mock_click):
    """アラームのスレッドは SIGINT を受け取らない状態で起動する。

    受け取られると、後始末の最中でもメインスレッドへ
    KeyboardInterrupt が飛び、SIGKILL の前に抜けてしまう。
    スレッドは生成時のマスクを継ぐので、**start() がマスクの内側で
    起きること**まで固定する。

    戻すときは解除ではなく、元のマスクへ戻す（呼ぶ側が SIGINT を
    止めていることがあるため）。
    """
    timer.alarm_params = AlarmParams(0, 0.0, 0.0)  # すぐ終わる
    timer.alarm_active = True

    manager = MagicMock()  # 呼び出し順をまとめて見る
    with (
        patch("tmr.timer.signal.pthread_sigmask") as mock_mask,
        patch("tmr.timer.threading.Thread") as mock_thread,
    ):
        mock_mask.return_value = {signal.SIGUSR1}  # 元のマスク
        manager.attach_mock(mock_mask, "mask")
        manager.attach_mock(mock_thread, "Thread")

        thr = timer.ring_alarm()

    assert thr is mock_thread.return_value
    assert [c[0] for c in manager.mock_calls] == [
        "Thread",
        "mask",
        "Thread().start",
        "mask",
    ]
    assert mock_mask.call_args_list == [
        ((signal.SIG_BLOCK, {signal.SIGINT}),),
        ((signal.SIG_SETMASK, {signal.SIGUSR1}),),
    ]


def test_cleanup_by_interrupt_restores_sigmask(timer, mock_click):
    """後始末はマスクの内側で行い、解除ではなく元のマスクへ戻す。

    呼ぶ側が SIGINT を止めていることがあるため
    （Timer をライブラリとして直接使う経路）。
    """
    timer.alarm_thr = MagicMock()

    manager = MagicMock()  # 呼び出し順をまとめて見る
    with (
        patch("tmr.timer.signal.pthread_sigmask") as mock_mask,
        patch.object(Timer, "stop_alarm_cmd") as mock_stop,
    ):
        mock_mask.return_value = {signal.SIGUSR1}  # 元のマスク
        manager.attach_mock(mock_mask, "mask")
        manager.attach_mock(mock_stop, "stop")

        timer.cleanup_by_interrupt()

    assert [c[0] for c in manager.mock_calls] == ["mask", "stop", "mask"]
    mock_stop.assert_called_once_with(timer.alarm_thr)
    assert mock_mask.call_args_list == [
        ((signal.SIG_BLOCK, {signal.SIGINT}),),
        ((signal.SIG_SETMASK, {signal.SIGUSR1}),),
    ]


def test_main_keyboard_interrupt_twice(
    timer, mock_click, mock_clock_time, mock_subprocess, mock_killpg
):
    """後始末の最中の 2 度目の Ctrl-C は無視して、止めきる。"""
    timer.alarm_params = AlarmParams(1, 0.001, 0.001, "sleep 5")
    mock_clock_time.monotonic.side_effect = [100.0, 110.0, 120.0]

    with patch.object(
        Timer, "get_key_name", side_effect=["", KeyboardInterrupt()]
    ):
        with patch.object(
            Timer, "stop_alarm_cmd", side_effect=KeyboardInterrupt()
        ) as mock_stop:
            timer.clock.t_limit = 0.1
            with pytest.raises(KeyboardInterrupt):
                timer.main()

    mock_stop.assert_called_once()


def test_main_keyboard_interrupt_without_alarm(
    timer, mock_click, mock_clock_time, mock_killpg
):
    """アラームに入る前の Ctrl-C は、そのまま送出し直すだけ。"""
    mock_clock_time.monotonic.side_effect = [100.0, 100.1]

    with patch.object(
        Timer, "get_key_name", side_effect=[KeyboardInterrupt()]
    ):
        with pytest.raises(KeyboardInterrupt):
            timer.main()

    assert timer.alarm_thr is None
    mock_killpg.assert_not_called()


def test_stop_alarm_cmd_beep(timer, mock_click):
    """ビープの経路（コマンド無し）では何もせず True。"""
    thr = MagicMock()
    assert timer.alarm_proc is None
    assert timer.stop_alarm_cmd(thr) is True
    assert timer.alarm_cmd_stopped is False


def test_main_stops_alarm_cmd_by_key(
    timer, mock_click, mock_clock_time, mock_subprocess, mock_killpg
):
    """キー入力でアラームを抜けたら、コマンドも止めてから返る。"""
    stop_event = threading.Event()
    proc = _running_proc(mock_subprocess, stop_event)
    mock_killpg.side_effect = lambda pid, sig: stop_event.set()

    timer.alarm_params = AlarmParams(1, 0.001, 0.001, "sleep 5")
    mock_clock_time.monotonic.side_effect = [100.0, 110.0, 120.0]

    with patch.object(Timer, "get_key_name", side_effect=["", "Q"]):
        timer.clock.t_limit = 0.1
        assert timer.main() is True

    mock_killpg.assert_called_once_with(proc.pid, signal.SIGTERM)
    assert stop_event.is_set()


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
