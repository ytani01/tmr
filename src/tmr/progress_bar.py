#
# (c) 2026 Yoichi Tanibayashi
#
import click
from loguru import logger

from . import ESQ_EL0


class ProgressBar:
    """Progress Bar."""

    DEF_BAR_LEN: int = 25  # chars

    DEF_CH_ON: str = ">"
    DEF_CH_OFF: str = "-"

    CH_HEAD = ["|", "/", "-", "\\"]
    # CH_HEAD = [">"]
    # CH_HEAD = ["<", "<", "<", "=", "="]

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

        self.ch_head_i = 0

    def get_str(
        self,
        val: float | None = None,
        *,
        bar_len: int = 0,
        stop: bool = False,
    ) -> str:
        """Display."""
        if val is not None:
            self.val = val
        if bar_len <= 0:
            bar_len = self.bar_len

        on_len: int = min(round(self.val / self.total * bar_len), bar_len)
        off_len = bar_len - on_len

        str_on = str_off = str_cur = ""

        # 風車
        if on_len >= 1:
            if self.val >= self.total or stop:
                str_cur = self.ch_on
            else:
                str_cur = self.CH_HEAD[self.ch_head_i]
                self.ch_head_i = (self.ch_head_i + 1) % len(self.CH_HEAD)

        if on_len >= 2:
            str_on = self.ch_on * (on_len - 1)

        if off_len > 0:
            str_off = self.ch_off * off_len

        return f"{ESQ_EL0}{str_on}{str_cur}{str_off}"

    def display(
        self,
        val: float | None = None,
        *,
        bar_len: int = 0,
        stop: bool = False,
        fg: str = "white",
        blink: bool = False,
    ):
        """Display."""
        sbar_str = self.get_str(val, bar_len=bar_len, stop=stop)

        click.secho(sbar_str, fg=fg, blink=blink, nl=False)
