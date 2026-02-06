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

ESC = "\x1b"  # == \033
SEQ_CSR_ON = f"{ESC}[?25h"  # Visible cursor
SEQ_CSR_OFF = f"{ESC}[?25l"  # Invisible cursor
SEQ_EL0 = f"{ESC}[0K"  # Erase in line: カーソルから行末まで削除


__all__ = [
    "__version__",
    "logger",
    "SEC_MIN",
]
