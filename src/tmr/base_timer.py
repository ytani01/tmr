#
# (c) 2026 Yoichi Tanibayashi
#
import threading
import time

import click
from loguru import logger
from rich.progress import Progress


class BaseTimer:
    """Base Timer."""

    COUNT_MANY = 999
    SEC_MIN = 60  # secs per minute
    TIME_FMT = "%m/%d %T"
    TICK = 0.1  # sec
    CH_ESC = "\x1b"

    def __init__(
        self,
        t_limit_min: float,
        *,
        prefix=("Timer", "green"),
        msg: str = "Press any key ..",
        alarm_params=(COUNT_MANY, 0.5, 1.5),
    ):
        """Constractor."""
        logger.debug(
            f"t_limit_min={t_limit_min}, "
            f"prefix={prefix}, "
            f"msg='{msg}', "
            f"alarm_params={alarm_params}"
        )

        self.t_limit = t_limit_min * self.SEC_MIN  # sec
        self.prefix = prefix[0]
        self.pf_color = prefix[1]
        self.msg = msg
        self.alarm_params = alarm_params

        self.alarm_active = True

    def main(self):
        """Main."""
        logger.debug("")

        self.alarm_active = True

        # プログレスバー生成
        with Progress() as progress:
            task = progress.add_task("", total=self.t_limit)

            try:
                # start update loop
                t_start = time.time()  # 開始時間
                while not progress.finished:
                    t_elapsed = time.time() - t_start  # 経過時間
                    t_remain = self.t_limit - t_elapsed
                    if t_remain < 0:
                        t_remain = 0.0

                    # 分、秒に分解
                    t_e_min, t_e_sec = divmod(t_elapsed, self.SEC_MIN)
                    t_r_min, t_r_sec = divmod(t_remain, self.SEC_MIN)
                    t_l_min, t_l_sec = divmod(self.t_limit, self.SEC_MIN)

                    # プログレスバーの行頭の文字列
                    desc_str = (
                        f"{time.strftime(self.TIME_FMT)} "
                        f"[{self.pf_color}]{self.prefix}[/{self.pf_color}] "
                        f"{t_e_min:.0f}:{t_e_sec:02.0f}"
                        f"(-{t_r_min:.0f}:{t_r_sec:02.0f})"
                        f"/{t_l_min:.0f}:{t_l_sec:02.0f} "
                    )

                    progress.update(
                        task, completed=t_elapsed, description=desc_str
                    )

                    time.sleep(self.TICK)

            except KeyboardInterrupt as e:
                logger.debug(f"{type(e).__name__}")
                self.alarm_active = False

        self.ring_alarm()

        if self.msg:
            click.echo(self.msg, nl=False)

        # 入力待ち
        ch = click.getchar()
        # logger.debug(f"ch={ch.encode('utf-8')}")
        logger.debug(f"ch={ch!r}")

        if ch == self.CH_ESC:
            # [ESC] で、終了
            raise KeyboardInterrupt

        # サブスレッドのアラームを停止
        self.alarm_active = False

        if self.msg:
            click.echo(
                f"\r{time.strftime(self.TIME_FMT)} Done.                    ",
                nl=False,
            )

    def alarm(self, count, sec1, sec2):
        """Alarm thread function."""
        logger.debug(f"count={count},sec1={sec1},sec2={sec2}")
        for _ in range(count):
            if not self.alarm_active:
                logger.debug(f"alarm_active={self.alarm_active}")
                break

            click.echo("\a", nl=False)
            time.sleep(sec1)
            click.echo("\a", nl=False)
            time.sleep(sec2)

        self.alarm_active = True

    def ring_alarm(self):
        """Ring alarm.

        make thread and start.
        """
        logger.debug(f"alarm_params={self.alarm_params}")

        threading.Thread(
            target=self.alarm, args=self.alarm_params, daemon=True
        ).start()
