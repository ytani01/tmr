#
# (c) 2026 Yoichi Tanibayashi
#
import math
from collections.abc import Iterator
from dataclasses import dataclass

from .mylog import getLogger
from .timer import AlarmParams, Timer
from .view import TimerTitle

_log = getLogger("pomodoro")


@dataclass(frozen=True)
class PomodoroConfig:
    work_sec: float
    break_sec: float
    long_break_sec: float
    cycles: int
    alarm_params: AlarmParams = Timer.DEF_ALARM

    def __post_init__(self) -> None:
        """各フィールドの妥当性を確認する。"""
        # 時間のフィールドを足したら、ここにも足す
        for name in ("work_sec", "break_sec", "long_break_sec"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(
                    f"{name} must be a finite number > 0: {name}={value}"
                )

        if self.cycles < 1:
            raise ValueError(f"cycles must be >= 1: cycles={self.cycles}")


TITLE_WIDTH = 16


def phases(config: PomodoroConfig) -> Iterator[tuple[TimerTitle, float]]:
    """フェーズの並びを、無限に返す。"""
    _log.debug(f"config={config}")

    while True:
        for i in range(config.cycles):
            # Work
            yield (
                TimerTitle(
                    f"WORK:{i + 1}/{config.cycles}", "cyan", TITLE_WIDTH
                ),
                config.work_sec,
            )

            # Break
            if i < config.cycles - 1:
                # Short Break
                yield (
                    TimerTitle(
                        f"SHORT_BREAK:{i + 1}/{config.cycles}",
                        "yellow",
                        TITLE_WIDTH,
                    ),
                    config.break_sec,
                )
            else:
                # Long Break
                yield (
                    TimerTitle(
                        f"LONG_BREAK:{i + 1}/{config.cycles}",
                        "red",
                        TITLE_WIDTH,
                    ),
                    config.long_break_sec,
                )


class PomodoroTimer:
    """Pomodoro Timer"""

    __log = getLogger(__qualname__)

    def __init__(self, config: PomodoroConfig):
        self.__log.debug(f"config={config}")

        self.config = config

    def run(self) -> bool:
        """ポモドーロサイクルの実行

        Returns:
            bool: ユーザが中断(quit)した場合は True、それ以外は False
        """
        self.__log.debug("")

        for title, sec in phases(self.config):
            if self._run_timer(title, sec):
                return True  # Quit

        return False

    def _run_timer(self, title: TimerTitle, seconds: float) -> bool:
        """単発タイマーの実行

        Returns:
            bool: Timer.main() の戻り値 (True=Quit)
        """
        self.__log.debug(f"title={title}, seconds={seconds}")

        timer = Timer(
            title,
            seconds,
            alarm_params=self.config.alarm_params,
            enable_next=True,
        )
        return timer.main()
