#
# (c) 2026 Yoichi Tanibayashi
#
"""時間の単位と、時間の文字列表示。"""

SEC_MIN = 60  # seconds per minute
MIN_HOUR = 60  # minutes per hour


def t_str(sec: float, omit_sec: bool = False) -> str:
    """Time string.

    sec -> "M:SS"
    """
    m, s = divmod(sec, SEC_MIN)
    if m < MIN_HOUR:
        if omit_sec and s == 0:
            return f"{m:2.0f}m"
        return f"{m:2.0f}m{s:02.0f}s"

    h, m = divmod(m, MIN_HOUR)
    if omit_sec and s == 0:
        return f"{h:.0f}h{m:02.0f}m"

    return f"{h:.0f}h{m:02.0f}m{s:02.0f}s"
