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

    SEC_MIN = 60  # secs per minute
    TIME_FMT = "%m/%d %T"

    def __init__(
        self,
        setting_time: float,
        *,
        prefix=("Timer", "green"),
        msg: str = "",
        alarm_params=(3, 0.5, 1.5),
    ):
        """Constractor."""
        logger.debug(
            f"setting_time={setting_time}, "
            f"prefix={prefix}, "
            f"msg='{msg}', "
            f"alarm_params={alarm_params}"
        )

        self.setting_time = setting_time
        self.prefix = prefix[0]
        self.pf_color = prefix[1]
        self.msg = msg
        self.alarm_params = alarm_params

        self.alarm_active = True

    def main(self):
        """Main."""
        logger.debug("")

        t_start = time.time()

        with Progress() as progress:
            task = progress.add_task(
                "", total=self.setting_time * self.SEC_MIN
            )
            while not progress.finished:
                t_elapsed = time.time() - t_start

                desc_str = (
                    f"{time.strftime(self.TIME_FMT)} "
                    f"[{self.pf_color}]{self.prefix}[/{self.pf_color}] "
                    f"{t_elapsed:.0f}/{self.setting_time * self.SEC_MIN:.0f}s:"
                )

                progress.update(
                    task, completed=t_elapsed, description=desc_str
                )

                time.sleep(0.1)

        self.alarm_active = True
        self.ring()

        if self.msg:
            click.echo("Press any key to stop alarm ..", nl=False)

        ch = click.getchar()
        logger.debug(f"ch='{ch}'")

        self.alarm_active = False

        if self.msg:
            click.echo(f"\r{time.strftime(self.TIME_FMT)} Done.          ")

    def alarm(self, count, sec1, sec2):
        """Alarm."""
        for _ in range(count):
            if not self.alarm_active:
                break

            click.echo("\a", nl=False)
            time.sleep(sec1)
            click.echo("\a", nl=False)
            time.sleep(sec2)

        self.alarm_active = True

    def ring(self):
        """Ring."""
        logger.debug(f"alarm_params={self.alarm_params}")

        threading.Thread(
            target=self.alarm, args=self.alarm_params, daemon=True
        ).start()
