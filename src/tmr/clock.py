#
# (c) 2026 Yoichi Tanibayashi
#
"""タイマーの時刻管理（端末に依存しない部分）。"""

import time

from .mylog import getLogger


class TimerClock:
    """Timer clock.

    早送り・巻き戻し・ポーズは ``t_start`` をずらして表現する
    （``elapsed`` を直接いじらない）。
    """

    __log = getLogger(__qualname__)

    def __init__(self, t_limit: float):
        """Constructor."""
        self.__log.debug(f"t_limit={t_limit}")

        self.t_limit = t_limit
        self.t_start = 0.0
        self.elapsed = 0.0
        self.is_paused = False

    def start(self) -> None:
        """計測を開始する。"""
        self.__log.debug("")

        self.t_start = time.monotonic()
        self.elapsed = 0.0
        self.is_paused = False

    def tick(self) -> None:
        """経過時間を更新する（メインループから毎周回呼ぶ）。"""
        t_cur = time.monotonic()

        if self.is_paused:
            # ポーズ中は、self.elapsed を固定し、self.t_start を調整
            self.t_start = t_cur - self.elapsed
        else:
            self.elapsed = min(t_cur - self.t_start, self.t_limit)

    def toggle_pause(self) -> None:
        """ポーズを切り替える。"""
        self.is_paused = not self.is_paused
        self.__log.debug(f"is_paused={self.is_paused}")

    def forward(self, sec: float = 1.0) -> None:
        """早送りする。"""
        self.__log.debug(f"sec={sec}")

        t_cur = time.monotonic()
        self.t_start = max(self.t_start - sec, t_cur - self.t_limit)
        self.elapsed = t_cur - self.t_start

    def backward(self, sec: float = 1.0) -> None:
        """巻き戻す。"""
        self.__log.debug(f"sec={sec}")

        t_cur = time.monotonic()
        self.t_start = min(self.t_start + sec, t_cur)
        self.elapsed = t_cur - self.t_start

    @property
    def remain(self) -> float:
        """残り時間 [sec]。"""
        return max(self.t_limit - self.elapsed, 0)

    @property
    def rate(self) -> float:
        """経過率 [%]。"""
        return self.elapsed / self.t_limit * 100

    @property
    def is_timeup(self) -> bool:
        """タイマーが満了したか。"""
        return self.elapsed >= self.t_limit
