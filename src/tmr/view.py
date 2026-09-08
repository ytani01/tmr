#
# (c) 2026 Yoichi Tanibayashi
#
"""タイマーの表示。"""

import time
from dataclasses import dataclass

import click
from blessed import Terminal

from .clock import TimerClock
from .mylog import getLogger
from .progress_bar import ProgressBar
from .terminal import ESQ_EL2
from .timefmt import t_str


@dataclass(frozen=True)
class TimerTitle:
    """Timer title."""

    text: str
    color: str = "white"
    width: int = 0  # 0 なら整形しない

    @property
    def display_text(self) -> str:
        """表示用の文字列（width が正なら桁を揃える）。"""
        if self.width > 0:
            return f"{self.text:{self.width}s}"
        return self.text


@dataclass
class TimerCol:
    """Timer column.

    priority が小さいものから削られる。
    """

    name: str
    priority: int
    value: str = ""
    color: str = "white"
    rate_color: bool = False
    bold: bool = False
    pause_blink: bool = False
    use: bool = True


class TimerView:
    """Timer view."""

    __log = getLogger(__qualname__)

    STAT_STR_PAUSE = "[PAUSE]"
    STAT_STR_TIMEUP = "[TIME UP]"

    PERCENT_COLOR = {
        "white": 0,
        "yellow": 80,
        "red": 95,
    }

    PBAR_LEN_MIN = 10

    def __init__(self, term: Terminal, title: TimerTitle):
        """Constructor."""
        self.__log.debug(f"title={title}")

        self.term = term
        self.pbar = ProgressBar()

        self.col: dict[str, TimerCol] = {c.name: c for c in self.col_list()}
        self.col["title"].value = title.display_text
        self.col["title"].color = title.color

    def col_list(self) -> list[TimerCol]:
        """Column list.

        **リストの並びが表示順**、priority が削除の優先順位
        （小さいものから削られる）。
        """
        self.__log.debug("")
        return [
            TimerCol("date", 1),
            TimerCol("time", 2),
            TimerCol("title", 8, bold=True),
            TimerCol("limit", 5),
            TimerCol("state", 7, rate_color=True, pause_blink=True),
            TimerCol("rate", 4, rate_color=True, pause_blink=True),
            TimerCol("elapsed", 3, rate_color=True, pause_blink=True),
            TimerCol("pbar", 6, rate_color=True, pause_blink=True),
            TimerCol("remain", 9, rate_color=True, pause_blink=True),
        ]

    def all_len(self, names: list[str]) -> int:
        """表示する項目を並べたときの長さ。"""
        _len = 0
        for n in names:
            val = self.col[n].value
            if val:
                _len += len(val) + 1
        _len -= 1 if _len > 0 else 0
        return _len

    def display(
        self,
        clock: TimerClock,
        *,
        is_active: bool,
        alarm_active: bool,
    ) -> None:
        """Display."""
        self.col["date"].value = f"{time.strftime('%Y-%m-%d')}"
        self.col["time"].value = f"{time.strftime('%H:%M:%S')}"
        self.col["limit"].value = t_str(clock.t_limit, omit_sec=True)
        self.col["elapsed"].value = t_str(clock.elapsed)
        self.col["remain"].value = t_str(clock.remain)
        self.col["pbar"].value = "-" * self.PBAR_LEN_MIN  # 仮の値

        ## col["state"]
        self.col["state"].value = ""
        if clock.is_paused:
            self.col["state"].value = self.STAT_STR_PAUSE
        if clock.is_timeup and alarm_active:
            self.col["state"].value = self.STAT_STR_TIMEUP

        ## col["rate"]
        t_rate = clock.rate
        self.col["rate"].value = f"{round(t_rate, 1):5.1f}%"

        ## t_rate に応じて色を変更
        cur_rate_color = "white"
        for color, percent in self.PERCENT_COLOR.items():
            if t_rate >= percent:
                cur_rate_color = color

        for col in self.col.values():
            if col.rate_color:
                col.color = cur_rate_color

        # 表示項目（表示順のコピーを作成して操作）
        col_disp = list(self.col.keys())
        for col in self.col.values():
            col.use = True

        # 長過ぎる場合、優先度の低い項目から省略する
        del_order = sorted(self.col.values(), key=lambda c: c.priority)
        for col in del_order:
            if not col_disp or self.all_len(col_disp) <= self.term.width:
                break
            col_disp.remove(col.name)
            col.use = False

        if not col_disp:
            # 表示する項目がなくなった場合
            click.secho(f"\r{ESQ_EL2}!?", blink=True, nl=False)
            return

        # プログレスバーを表示する場合の処理
        if "pbar" in col_disp:
            # プログレスバーの長さ
            col_disp.remove("pbar")
            pbar_len = self.term.width - self.all_len(col_disp) - 1

            # ポーズ中・終了時は、風車を止める
            pbar_stop = clock.is_paused or (not is_active)

            # プログレスバー生成
            self.col["pbar"].value = self.pbar.get_str(
                clock.elapsed,
                clock.t_limit,
                bar_len=pbar_len,
                stop=pbar_stop,
            )

        # 表示する文字列を作成(スタイル付き)
        str_disp = "\r"
        for col in self.col.values():
            if not col.use or not col.value:
                continue

            f_blink = False
            if col.pause_blink and clock.is_paused:
                f_blink = True
            if col.name == "state" and clock.is_timeup:
                f_blink = True

            str_disp += click.style(
                col.value,
                fg=col.color,
                bold=col.bold,
                blink=f_blink,
            )
            str_disp += " "

        # 表示 ([:-1] .. 行末の " " は表示しない)
        click.echo(f"{ESQ_EL2}{str_disp[:-1]}", nl=False)
