#
# (c) 2026 Yoichi Tanibayashi
#
"""mylog.py

# sample

```python
from .mylog import loggerInit, exmsg

def main(debug: bool = False):
    logInit(debug=debug)
    logger.debug(debg)

    try:
     :
    except Exception as e:
      logger.error(exmsg(e))
```
"""

import os
import sys
from typing import TextIO

from loguru import logger

LOG_FMT = (
    "<level>"
    "<white>{time:MM/DD HH:mm:ss}</white> "
    "{level.icon} {level} "
    "{file}<green>:</green>{line} "
    "{function}()<green>></green> "
    "<white>{message}</white>"
    "</level>"
)

# TMR_LOG で指定できる名前のうち、実際に getLogger() で使われたもの。
_registered_names: set[str] = set()


def getLogger(name: str):
    """名前付きの logger を返す。

    モジュールの先頭に 1 つ置いて使う（``_log = getLogger("BaseTimer")``）。
    返り値は ``logger.bind()`` した束縛オブジェクトで、
    ``extra["log_name"]`` にこの名前が入る。
    """
    _registered_names.add(name)
    return logger.bind(log_name=name)


def logLevel(debug: bool = False) -> str:
    """ログの水準。``debug`` なら DEBUG、そうでなければ INFO。"""
    return "DEBUG" if debug else "INFO"


def _parse_tmr_log(env: str) -> dict[str, str]:
    """``TMR_LOG=BaseTimer=DEBUG,main=INFO`` を辞書にする。"""
    levels: dict[str, str] = {}
    for item in env.split(","):
        item = item.strip()
        if not item or "=" not in item:
            continue
        name, _, level = item.partition("=")
        levels[name.strip()] = level.strip().upper()
    return levels


def _make_filter(levels: dict[str, str]):
    def _filter(record) -> bool:
        name = record["extra"].get("log_name", record["name"])
        level_name = levels.get(name, levels.get("", "INFO"))
        return record["level"].no >= logger.level(level_name).no

    return _filter


def loggerInit(debug: bool = False, out: TextIO = sys.stderr) -> None:
    """logger を初期化する

    各 CLI コマンドの先頭で 1 度だけ呼ぶ。
    環境変数 ``TMR_LOG``（例: ``BaseTimer=DEBUG,main=INFO``）で
    名前ごとに水準を変えられる。ここで指定した名前が
    ``getLogger()`` で使われていなければ warning を出す。

    Parameters
    ----------
    debug: bool
        デバッグ出力を出すか（既定の水準）
    out
        出力先。既定は標準エラー
    """
    logger.remove()

    levels = {"": logLevel(debug)}
    unknown_names: list[str] = []
    for name, level_name in _parse_tmr_log(
        os.environ.get("TMR_LOG", "")
    ).items():
        if name and name not in _registered_names:
            unknown_names.append(name)
        levels[name] = level_name

    logger.add(out, level=0, filter=_make_filter(levels), format=LOG_FMT)

    for name in unknown_names:
        logger.warning(f"TMR_LOG: 知らない名前です: '{name}'")


def exmsg(ex: Exception) -> str:
    """例外を 1 行の文字列にする（``ValueError: 使えない名前です`` の形）。"""
    return f"{type(ex).__name__}: {ex}"
