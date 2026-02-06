#
# (c) 2026 Yoichi Tanibayashi
#
import threading
import time

import click
from blessed import Terminal
from loguru import logger

from . import MIN_HOUR, SEC_MIN
from .progress_bar import ProgressBar


class BaseTimer:
    """Base Timer."""

    KEYS = {
        "quit": ["q", "Q", "KEY_ESCAPE"],
        "pause": [" ", "KEY_ENTER"],
        "forward": ["+", "=", "KEY_RIGHT", "KEY_DOWN"],
        "backward": ["-", "_", "KEY_LEFT", "KEY_UP"],
    }

    COUNT_MANY = 999

    def __init__(
        self,
        title: tuple[str, str] = ("Timer", "white"),
        limit: float = 3.0,
        arlarm_params=(COUNT_MANY, 0.5, 1.5),
    ):
        """Constractor."""
        logger.debug(
            f"title={title},limit={limit},alarm_param={arlarm_params}"
        )

        self.title = title[0]
        self.title_color = title[1]
        self.limit = limit
        self.alarm_params = arlarm_params

        self.alarm_active = False

        self.pbar = ProgressBar(self.limit)

        self.term = Terminal()

    def main(self):
        """Main."""
        logger.debug("start.")

        with self.term.cbreak():
            t_start = time.monotonic()
            t_elapsed = 0.0

            is_active = True
            is_paused = False

            while is_active:
                # キー入力
                in_key = self.term.inkey(timeout=0.05)
                key_name = ""
                if in_key:
                    if in_key.name:
                        logger.debug(f"in_key={in_key.name}")
                        key_name = in_key.name  # key_nameに統一
                    else:
                        logger.debug(f"in_key={in_key!r}")
                        key_name = in_key  # key_nameに統一

                    # key_name による、処理
                    if key_name in self.KEYS["quit"]:
                        logger.debug("Quit")
                        # ここで break はしない
                        is_active = False
                        is_paused = False
                        self.alarm_active = False

                    if key_name in self.KEYS["pause"]:
                        if is_paused:
                            is_paused = False
                        else:
                            is_paused = True
                        logger.debug(f"is_paused={is_paused}")

                    if key_name in self.KEYS["forward"]:
                        t_cur = time.monotonic()
                        t_start = max(t_start - 1.0, t_cur - self.limit)
                        t_elapsed = min(t_elapsed + 1.0, self.limit)

                    if key_name in self.KEYS["backward"]:
                        t_cur = time.monotonic()
                        t_start = min(t_start + 1.0, t_cur)
                        t_elapsed = max(t_elapsed - 1.0, 0.0)

                # 時間経過
                t_cur = time.monotonic()

                if is_paused:
                    # ポーズ中は、t_elapsed を固定
                    # t_start を調整
                    t_start = t_cur - t_elapsed
                else:
                    t_elapsed = min(t_cur - t_start, self.limit)

                self.display(t_elapsed, is_paused)

                # 終了判定
                if t_elapsed >= self.limit:
                    if not is_paused:
                        self.alarm_active = True
                        break

        click.echo()

        if self.ring_alarm():  # アラーム
            click.echo("# Press any key to stop alarm..")

        with self.term.cbreak():
            while self.alarm_active:
                in_key = self.term.inkey(timeout=0.05)
                if not in_key:
                    continue
                logger.debug(f"in_key={in_key}")
                self.alarm_active = False

        logger.debug("done.")

    def t_str(self, sec: int | float) -> str:
        """Time string.

        sec -> "mm:ss"
        """
        m, s = divmod(sec, SEC_MIN)
        if m < MIN_HOUR:
            return f"{m:.0f}:{s:02.0f}"

        h, m = divmod(m, MIN_HOUR)
        return f"{h:.0f}:{m:02.0f}:{s:02.0f}"

    def display(self, t_elapsed: float, is_paused: bool):
        """Display."""
        t_remain = max(self.limit - t_elapsed, 0)
        t_rate = t_elapsed / self.limit * 100

        click.echo("\r", nl=False)
        click.echo(f"{time.strftime('%m/%d %H:%M:%S')} ", nl=False)
        click.secho(f"{self.title} ", fg=self.title_color, nl=False)
        click.secho(self.t_str(self.limit), bold=True, nl=False)
        click.echo("=", nl=False)
        click.secho(self.t_str(t_elapsed), blink=is_paused, nl=False)
        click.echo("+", nl=False)
        click.secho(self.t_str(t_remain), blink=is_paused, nl=False)
        click.echo(" ", nl=False)
        click.secho(f"{t_rate:3.0f}%", blink=is_paused, nl=False)
        click.echo(" ", nl=False)

        self.pbar.display(t_elapsed)

    def thr_alarm(self, count, sec1, sec2):
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

        self.alarm_active = False

    def ring_alarm(self) -> bool:
        """Ring alarm.

        make thread and start.
        """
        logger.debug(f"alarm_params={self.alarm_params}")

        if not self.alarm_active:
            return False

        threading.Thread(
            target=self.thr_alarm, args=self.alarm_params, daemon=True
        ).start()
        return True
