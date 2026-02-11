#
# (c) 2026 Yoichi Tanibayashi
#
from dataclasses import dataclass

from .base_timer import BaseTimer


@dataclass
class PomodoroConfig:
    work_sec: float
    break_sec: float
    long_break_sec: float
    cycles: int


class PomodoroCore:
    def __init__(self, config: PomodoroConfig):
        self.config = config

    def run(self) -> bool:
        """ポモドーロサイクルの実行

        Returns:
            bool: ユーザ中断(quit)があった場合は True、それ以外は False
        """
        while True:
            for i in range(self.config.cycles):
                # Work
                if self._run_timer("WORK", self.config.work_sec, "cyan"):
                    return True  # Quit

                # Break
                if i < self.config.cycles - 1:
                    # Short Break
                    if self._run_timer(
                        "SHORT_BREAK", self.config.break_sec, "yellow"
                    ):
                        return True  # Quit
                else:
                    # Long Break
                    if self._run_timer(
                        "LONG_BREAK", self.config.long_break_sec, "red"
                    ):
                        return True  # Quit

            # forループが中断されずに完了した場合、whileループで次のサイクルへ
            # (現状の仕様通り、無限に繰り返す)

    def _run_timer(self, title_text: str, seconds: float, color: str) -> bool:
        """単発タイマーの実行

        Returns:
            bool: BaseTimer.main() の戻り値 (True=Quit)
        """
        timer = BaseTimer((title_text, color), seconds, enable_next=True)
        return timer.main()
