#
# (c) 2026 Yoichi Tanibayashi
#
from importlib.metadata import PackageNotFoundError, version

from loguru import logger

if __package__:
    try:
        __version__ = version(__package__)
    except PackageNotFoundError:
        __version__ = "0.0.0"
else:
    __version__ = "_._._"

SEC_MIN = 60
MIN_HOUR = 60

CH_ESC = "\x1b"  # == \033
SEQ_CURSOR_ON = f"{CH_ESC}[?25h"
SEQ_CURSOR_OFF = f"{CH_ESC}[?25l"
SEQ_EL0 = f"{CH_ESC}[0K"  # Erase in line: カーソルから行末まで削除


__all__ = [
    "__version__",
    "logger",
    "SEC_MIN",
]
