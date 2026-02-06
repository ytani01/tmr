#
# (c) 2026 Yoichi Tanibayashi
#
import click
from loguru import logger


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

    def display(self, val: float | None = None):
        """Display."""
        if val is not None:
            self.val = val

        on_len: int = min(
            int(self.val / self.total * self.bar_len), self.bar_len
        )
        off_len = self.bar_len - on_len

        for _ in range(on_len):
            click.echo(self.ch_on, nl=False)
        for _ in range(off_len):
            click.echo(self.ch_off, nl=False)
        click.echo("\r", nl=False)
