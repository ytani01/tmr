#
# (c) 2026 Yoichi Tanibayashi
#
from tmr.timefmt import t_str


def test_t_str_minutes_with_seconds():
    assert t_str(65) == " 1m05s"


def test_t_str_minutes_omit_sec():
    assert t_str(60, omit_sec=True) == " 1m"


def test_t_str_minutes_omit_sec_with_remainder():
    """omit_sec でも、秒が 0 でなければ秒を出す。"""
    assert t_str(65, omit_sec=True) == " 1m05s"


def test_t_str_hours():
    assert t_str(3661) == "1h01m01s"


def test_t_str_hours_omit_sec():
    assert t_str(3660, omit_sec=True) == "1h01m"


def test_t_str_zero():
    assert t_str(0) == " 0m00s"


def test_t_str_boundary_59_to_60_seconds():
    """59 秒はそのまま、60 秒は 1m00s へ繰り上がる。"""
    assert t_str(59) == " 0m59s"
    assert t_str(60) == " 1m00s"
