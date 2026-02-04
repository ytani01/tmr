#
# (c) 2026 Yoichi Tanibayashi
#
from importlib.metadata import PackageNotFoundError, version

from loguru import logger

from .click_utils import click_common_opts
from .mylog import LOG_FMT, logLevel

if __package__:
    try:
        __version__ = version(__package__)
    except PackageNotFoundError:
        __version__ = "0.0.0"
else:
    __version__ = "_._._"

__all__ = [
    "__version__",
    "click_common_opts",
    "logger",
    "LOG_FMT",
    "logLevel",
]
