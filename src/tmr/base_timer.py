#
# (c) 2026 Yoichi Tanibayashi
#
import click
import threading
import time
from loguru import logger
from rich.progress import Progress
from rich.console import Console


class BaseTimer:
    """Base Timer."""

    SEC_MIN = 60  # secs per minute
    
    def __init__(
        self,
        setting_time: float,
        prefix: str = "Timer",
        pf_color: str = "green",
        alarm_params = (3, 0.5, 1.5)
    ):
        """Constractor."""
        logger.debug((
            f"setting_time={setting_time},"
            f"prefix={prefix},{pf_color},"
            f"alarm_params={alarm_params}"
        ))

        self.setting_time = setting_time
        self.prefix = prefix
        self.pf_color = pf_color
        self.alarm_params = alarm_params

    def main(self):
        """Main."""
        logger.debug("")

        t_start = time.time()
        with Progress() as progress:
            task = progress.add_task("", total=self.setting_time*self.SEC_MIN)
            while not progress.finished:
                t_elapsed = time.time() - t_start

                desc_str = (
                    f"[{self.pf_color}]{self.prefix}[/{self.pf_color}]:"
                    f"{t_elapsed:4.0f}/{self.setting_time*60:.0f}:"
                )

                progress.update(
                    task,
                    completed=t_elapsed,
                    description=desc_str
                )

                time.sleep(.1)

        self.ring()
        click.pause("Press any key to stop alarm..")

    def alarm(self, count, sec1, sec2):
        """Alarm."""
        for _ in range(count):
            click.echo("\a", nl=False)
            time.sleep(sec1)
            click.echo("\a", nl=False)
            time.sleep(sec2)

    def ring(self):
        """Ring."""
        logger.debug(f"alarm_params={self.alarm_params}")

        threading.Thread(
            target=self.alarm, args=self.alarm_params, daemon=True
        ).start()
