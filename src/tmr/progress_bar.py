#
# (c) 2026 Yoichi Tanibayashi
#
import click
from loguru import logger

from . import SEQ_EL0


class ProgressBar:
    """Progress Bar."""

    DEF_BAR_LEN: int = 25  # chars

    DEF_CH_ON: str = ">"
    DEF_CH_OFF: str = "-"

    def __init__(
        self,
        total: float = 100.0,
        bar_length: int = DEF_BAR_LEN,
        ch: tuple[str, str] = (DEF_CH_ON, DEF_CH_OFF),
    ):
        """Constractor."""
        logger.debug(f"total={total}")

        self.bar_len: int = bar_length
        self.total: float = total
        self.ch_on: str = ch[0]
        self.ch_off: str = ch[1]

        self.val: float = 0.0

    def display(self, val: float | None = None, bar_len: int = 0):
        """Display."""
        if val is not None:
            self.val = val
        if bar_len <= 0:
            bar_len = self.bar_len

        on_len: int = min(round(self.val / self.total * bar_len), bar_len)
        off_len = bar_len - on_len

        click.echo(
            f"{SEQ_EL0}{self.ch_on * on_len}{self.ch_off * off_len}\r",
            nl=False,
        )
