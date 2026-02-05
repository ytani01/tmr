#
# (c) 2026 Yoichi Tanibayashi
#
import time

import click
from blessed import Terminal
from loguru import logger

from . import SEC_MIN
from .progress_bar import ProgressBar


class BaseTimer:
    """Base Timer."""

    def __init__(self, title: str, title_color: str, limit: float):
        """Constractor."""
        logger.debug(f"title={title},limit={limit}")

        self.title = title
        self.title_color = title_color
        self.limit = limit

        self.pbar = ProgressBar(self.limit)

        self.term = Terminal()

    def main(self):
        """Main."""
        logger.debug("start.")

        with self.term.cbreak():
            t_start = time.monotonic()
            t_elapsed = 0.0
            t_remain = self.limit
            is_active = True
            is_paused = False

            while is_active:
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
                    if key_name in ["q", "Q", "KEY_ESCAPE"]:
                        logger.debug("Quit")
                        # ここで break はしない
                        is_active = False
                        is_paused = False

                    if key_name in [" "]:
                        if is_paused:
                            is_paused = False
                        else:
                            is_paused = True
                        logger.debug(f"is_paused={is_paused}")

                    if key_name in ["-", "_"]:
                        t_cur = time.monotonic()
                        t_start = min(t_start + 1.0, t_cur)
                        t_elapsed = max(t_elapsed - 1.0, 0.0)

                    if key_name in ["+", "="]:
                        t_cur = time.monotonic()
                        t_start = max(t_start - 1.0, t_cur - self.limit)
                        t_elapsed = min(t_elapsed + 1.0, self.limit)

                t_cur = time.monotonic()

                if is_paused:
                    # ポーズ中は、t_elapsed を固定
                    # t_start を調整
                    t_start = t_cur - t_elapsed
                else:
                    t_elapsed = min(t_cur - t_start, self.limit)
                t_remain = max(self.limit - t_elapsed, 0)

                limit_m, limit_s = divmod(self.limit, SEC_MIN)
                elapsed_m, elapsed_s = divmod(t_elapsed, SEC_MIN)
                remain_m, remain_s = divmod(t_remain, SEC_MIN)

                click.echo("\r", nl=False)
                click.echo(f"{time.strftime('%m/%d %H:%M:%S')} ", nl=False)
                click.secho(
                    f"[{self.title}] ",
                    fg=self.title_color,
                    blink=is_paused,
                    nl=False,
                )
                click.secho(
                    (
                        f"{elapsed_m:.0f}:{elapsed_s:02.0f}"
                        f"(-{remain_m:.0f}:{remain_s:02.0f}) "
                        f"/ {limit_m:.0f}:{limit_s:02.0f} "
                        f"{t_elapsed / self.limit * 100:3.0f}% "
                    ),
                    blink=is_paused,
                    nl=False,
                )

                self.pbar.display(t_elapsed)

                if t_elapsed >= self.limit:
                    if not is_paused:
                        break

        click.echo()
        logger.debug("done.")
