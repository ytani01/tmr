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

__all__ = [
    "__version__",
    "logger",
    "SEC_MIN",
]
