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

SEC_MIN = 60  # seconds per minute
MIN_HOUR = 60  # minutes per hour

ESC = "\x1b"  # == \033, Escape
ESQ_CSR_ON = f"{ESC}[?25h"  # Visible cursor
ESQ_CSR_OFF = f"{ESC}[?25l"  # Invisible cursor
ESQ_EL0 = f"{ESC}[0K"  # Erase in line: カーソルから行末まで削除
ESQ_EL1 = f"{ESC}[1K"  # Erase in line: 行頭からカーソルまで削除
ESQ_EL2 = f"{ESC}[2K"  # Erase in line: 行全体を削除


__all__ = [
    "__version__",
    "logger",
    "SEC_MIN",
    "MIN_HOUR",
    "ESC",
    "ESQ_CSR_ON",
    "ESQ_CSR_OFF",
    "ESQ_EL0",
]
