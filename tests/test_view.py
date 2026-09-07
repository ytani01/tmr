#
# (c) 2026 Yoichi Tanibayashi
#
from unittest.mock import MagicMock, patch

import pytest

from tmr.clock import TimerClock
from tmr.view import TimerTitle, TimerView


@pytest.fixture
def mock_pbar():
    with patch("tmr.view.ProgressBar") as mock:
        mock.return_value.get_str.return_value = "----------"
        yield mock


@pytest.fixture
def mock_click():
    with patch("tmr.view.click") as mock:
        mock.style.side_effect = lambda text, **_kwargs: text
        yield mock


@pytest.fixture
def term():
    mock_term = MagicMock()
    mock_term.width = 80
    mock_term.height = 24
    return mock_term


@pytest.fixture
def view(term, mock_pbar, mock_click):
    """Fixture for TimerView with mocked dependencies."""
    _ = (mock_pbar, mock_click)
    return TimerView(term, 180.0, TimerTitle("Timer", "white"))


@pytest.fixture
def clock():
    return TimerClock(180.0)


def show(view, clock, *, is_active=True, alarm_active=False):
    """display() の呼び出しを短く書くための補助。"""
    view.display(clock, is_active=is_active, alarm_active=alarm_active)


def test_init(view, mock_pbar):
    """ProgressBar は TimerView が作る。"""
    assert view.pbar == mock_pbar.return_value
    assert view.col["title"].value == "Timer"
    assert view.col["title"].color == "white"


def test_col_order(view):
    """col の並びが表示順。"""
    assert list(view.col.keys()) == [
        "date",
        "time",
        "title",
        "limit",
        "state",
        "rate",
        "elapsed",
        "pbar",
        "remain",
    ]


def test_title_width():
    """TimerTitle.width で桁を揃える。"""
    assert TimerTitle("WORK:1/2").display_text == "WORK:1/2"
    assert TimerTitle("WORK:1/2", "cyan", 16).display_text == (
        "WORK:1/2        "
    )


def test_title_width_in_col(term, mock_pbar, mock_click):
    """桁を揃えたタイトルが col に入る。"""
    _ = (mock_pbar, mock_click)
    view = TimerView(term, 60.0, TimerTitle("WORK:1/2", "cyan", 16))
    assert view.col["title"].value == "WORK:1/2        "
    assert view.col["title"].color == "cyan"


def test_responsive_layout(view, clock):
    """幅が狭いと項目が省略される。"""
    # 広い幅: 全てのカラムが使われるはず
    view.term.width = 200
    show(view, clock)
    assert all(col.use for col in view.col.values())

    # 非常に狭い幅: 一部のカラムが disabled になるはず
    view.term.width = 10
    show(view, clock)
    assert view.col["date"].use is False
    assert view.col["time"].use is False

    # 超極小幅: 全て消える
    view.term.width = 1
    show(view, clock)
    assert not any(col.use for col in view.col.values())


def test_delete_order(view, clock):
    """削られる順番。"""
    # state に値を持たせる（空だと幅に影響せず、順番が観測できない）
    clock.is_paused = True

    removed: list[str] = []
    for width in range(200, -1, -1):
        view.term.width = width
        show(view, clock)
        for name, col in view.col.items():
            if not col.use and name not in removed:
                removed.append(name)

    assert removed == [
        "date",
        "time",
        "elapsed",
        "rate",
        "limit",
        "pbar",
        "state",
        "title",
        "remain",
    ]


def test_no_col(view, clock, mock_click):
    """項目が無くなったら '!?' を表示する。"""
    view.term.width = 0
    show(view, clock)
    mock_click.secho.assert_called_with("\r\x1b[2K!?", blink=True, nl=False)


def test_rate_color(view, clock):
    """経過率に応じて色が変わる。"""
    clock.t_limit = 100.0

    # 0% - white
    clock.elapsed = 0.0
    show(view, clock)
    assert view.col["remain"].color == "white"

    # 85% - yellow
    clock.elapsed = 85.0
    show(view, clock)
    assert view.col["remain"].color == "yellow"

    # 96% - red
    clock.elapsed = 96.0
    show(view, clock)
    assert view.col["remain"].color == "red"


def test_display_pause_state(view, clock):
    """ポーズ中は [PAUSE]。"""
    clock.t_limit = 60.0
    clock.elapsed = 10.0

    clock.is_paused = False
    show(view, clock)
    assert view.col["state"].value == ""

    clock.is_paused = True
    show(view, clock)
    assert view.col["state"].value == "[PAUSE]"


def test_display_timeup_state(view, clock):
    """満了かつアラーム中は [TIME UP]。"""
    clock.t_limit = 60.0
    clock.elapsed = 60.0

    show(view, clock, is_active=False, alarm_active=False)
    assert view.col["state"].value == ""

    show(view, clock, is_active=False, alarm_active=True)
    assert view.col["state"].value == "[TIME UP]"


def test_display_hours(view, clock):
    """1時間以上の表示。"""
    # 1 hour + 1 minute + 1 second = 3661 seconds
    clock.t_limit = 3661.0
    clock.elapsed = 0.0
    show(view, clock)
    assert view.col["limit"].value == "1h01m01s"

    clock.elapsed = 3661.0
    show(view, clock)
    assert view.col["elapsed"].value == "1h01m01s"


def test_empty_title(view, clock, mock_click):
    """タイトルが空でも落ちない。"""
    view.col["title"].value = ""
    view.term.width = 80
    show(view, clock)
    assert mock_click.echo.called


def test_pbar_stop(view, clock, mock_pbar):
    """ポーズ中・終了時は風車を止める。"""
    view.term.width = 200

    show(view, clock, is_active=True)
    assert mock_pbar.return_value.get_str.call_args[1]["stop"] is False

    show(view, clock, is_active=False)
    assert mock_pbar.return_value.get_str.call_args[1]["stop"] is True

    clock.is_paused = True
    show(view, clock, is_active=True)
    assert mock_pbar.return_value.get_str.call_args[1]["stop"] is True
