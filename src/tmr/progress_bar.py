#
# (c) 2026 Yoichi Tanibayashi
#
import click
from loguru import logger


class ProgressBar:
    """Progress Bar."""

    DEF_BAR_LEN: int = 25  # chars

    DEF_CH_ON: str = ">"
    DEF_CH_OFF: str = "_"
    DEF_CH_HEAD = ["|", "/", "-", "\\"]

    def __init__(
        self,
        total: float = 100.0,
        bar_length: int = DEF_BAR_LEN,
        ch: tuple[str, str] = (DEF_CH_ON, DEF_CH_OFF),
        ch_head: list[str] = DEF_CH_HEAD,
    ):
        """Constractor."""
        logger.debug(f"total={total}")

        self.bar_len: int = bar_length
        self.total: float = total
        self.ch_on: str = ch[0]
        self.ch_off: str = ch[1]
        self.ch_head = ch_head

        self.ch_head_i = 0

    def get_str(
        self,
        val: float,
        *,
        bar_len: int | None = None,
        stop: bool = False,
    ) -> str:
        """Display."""
        if bar_len is None:
            bar_len = self.bar_len

        if bar_len <= 0:
            return ""

        rate = val / self.total if self.total > 0 else 1.0
        on_len: int = max(0, min(round(rate * bar_len), bar_len))
        off_len = bar_len - on_len

        str_on = str_off = str_cur = ""

        # 風車 (0% でも動作中であることを示す)
        if val >= self.total or stop:
            if on_len >= 1:
                str_cur = self.ch_on
        else:
            str_cur = self.ch_head[self.ch_head_i]
            self.ch_head_i = (self.ch_head_i + 1) % len(self.ch_head)
            if on_len == 0:
                off_len = max(0, off_len - 1)  # スピナー分を差し引く

        if on_len >= 2:
            str_on = self.ch_on * (on_len - 1)

        if off_len > 0:
            str_off = self.ch_off * off_len

        return f"{str_on}{str_cur}{str_off}"

    def display(
        self,
        val: float,
        *,
        bar_len: int | None = None,
        stop: bool = False,
        fg: str = "white",
        blink: bool = False,
    ):
        """Display."""
        sbar_str = self.get_str(val, bar_len=bar_len, stop=stop)

        click.secho(sbar_str, fg=fg, blink=blink, nl=False)
