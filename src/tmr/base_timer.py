#
# (c) 2026 Yoichi Tanibayashi
#
import threading
import time
from dataclasses import dataclass
from typing import Callable, List

import click
from blessed import Terminal
from loguru import logger

from . import ESQ_EL0, MIN_HOUR, SEC_MIN
from .progress_bar import ProgressBar


@dataclass
class TimerCol:
    """Timer column."""

    value: str = ""
    color: str = "white"
    bold: bool = False
    use: bool = True
    blink: bool = False


@dataclass
class TimerCmd:
    """Timer Command."""

    info: str
    keys: List[str]
    fn: Callable[[], None]  # []:引数なし、 None:戻り値なし


class BaseTimer:
    """Base Timer."""

    IN_KEY_TIMEOUT = 0.2  # sec

    DEF_TITLE = ("Timer", "white")
    DEF_LIMIT = 180.0  # seconds
    COUNT_MANY = 999
    DEF_SEC1 = 0.5
    DEF_SEC2 = 1.5

    def __init__(
        self,
        title: tuple[str, str] = DEF_TITLE,
        t_limit: float = DEF_LIMIT,
        arlarm_params=(COUNT_MANY, DEF_SEC1, DEF_SEC2),
    ):
        """Constractor."""
        logger.debug(
            f"title={title},limit={t_limit},alarm_param={arlarm_params}"
        )

        self.col: dict = self.col_list()

        self.col["title"].value = title[0]
        self.col["title"].color = title[1]
        self.t_limit = t_limit
        self.alarm_params = arlarm_params

        self.t_start = 0.0
        self.t_elapsed = 0.0

        self.is_active = False
        self.is_paused = False
        self.alarm_active = False

        self.pbar = ProgressBar(self.t_limit)

        self.term = Terminal()
        logger.debug(f"term size:{self.term.width}x{self.term.height}")

        self.cmd: List[TimerCmd] = self.cmd_list()
        # self.cmd を {"key": fn} の形式に展開する。
        # fn = self.key_map["key"] となる。
        self.key_map = {k: item.fn for item in self.cmd for k in item.keys}

    def col_list(self) -> dict:
        """Column list."""
        logger.debug("")
        return {  # **重要**: 表示順にすること
            "date": TimerCol(),
            "title": TimerCol(bold=True),
            "limit": TimerCol(),
            "state": TimerCol(blink=True),
            "rate": TimerCol(blink=True),
            "elapsed": TimerCol(blink=True),
            "pbar": TimerCol(blink=True),
            "remain": TimerCol(blink=True),
        }

    def cmd_list(self) -> List[TimerCmd]:
        """Get command list as dataclass instances."""
        logger.debug("")
        return [
            TimerCmd(
                info="pause timer.",
                keys=[" ", "KEY_ENTER"],
                fn=self.fn_pause,
            ),
            TimerCmd(
                info="forward 1 second.",
                keys=["+", "=", "KEY_RIGHT", "KEY_CTRL_F"],
                fn=lambda: self.fn_forward(1.0),
            ),
            TimerCmd(
                info="backward 1 second.",
                keys=["-", "_", "KEY_LEFT", "KEY_CTRL_B"],
                fn=lambda: self.fn_backward(1.0),
            ),
            TimerCmd(
                info="foward 10 seconds.",
                keys=["KEY_DOWN", "KEY_CTRL_N"],
                fn=lambda: self.fn_forward(10.0),
            ),
            TimerCmd(
                info="backward 10 seconds.",
                keys=["KEY_UP", "KEY_CTRL_P"],
                fn=lambda: self.fn_backward(10.0),
            ),
            TimerCmd(
                info="clear terminal.",
                keys=["KEY_CTRL_L"],
                fn=click.clear,
            ),
            TimerCmd(
                info="quit.",
                keys=["q", "Q", "KEY_ESCAPE"],
                fn=self.fn_quit,
            ),
        ]

    def main(self):
        """Main."""
        logger.debug("start.")

        self.t_start = time.monotonic()
        self.t_elapsed = 0.0

        self.is_active = True
        self.is_paused = False

        with self.term.cbreak():
            # メインループ
            while self.is_active:
                key_name = self.get_key_name()  # キー入力
                if key_name:
                    logger.debug(f"key_name={key_name}")
                # キーマップに登録されているメソッドを呼び出す
                if key_name in self.key_map:
                    self.key_map[key_name]()

                # 時間経過
                t_cur = time.monotonic()

                if self.is_paused:
                    # ポーズ中は、self.t_elapsed を固定し、self.t_start を調整
                    self.t_start = t_cur - self.t_elapsed
                else:
                    self.t_elapsed = min(t_cur - self.t_start, self.t_limit)

                # 表示
                self.display()

                # 終了判定
                if self.t_elapsed >= self.t_limit:
                    if not self.is_paused:
                        self.is_active = False
                        self.alarm_active = True

        click.echo()

        if self.ring_alarm():  # アラーム alarm_active によっては鳴らない
            click.echo(" Press any key to stop alarm..")

        with self.term.cbreak():
            while self.alarm_active:
                in_key = self.term.inkey(timeout=self.IN_KEY_TIMEOUT)
                if not in_key:
                    continue
                logger.debug(f"in_key={in_key}")
                self.alarm_active = False

        logger.debug("done.")

    def get_key_name(self) -> str:
        """Get key name."""
        in_key = self.term.inkey(timeout=self.IN_KEY_TIMEOUT)
        key_name = ""
        if in_key:
            # key_name に統一
            if in_key.name:
                logger.debug(f"in_key={in_key.name}")
                key_name = in_key.name  # key_nameに統一
            else:
                logger.debug(f"in_key={in_key!r}")
                key_name = in_key  # key_nameに統一
        return key_name

    def fn_quit(self):
        logger.debug("")
        self.is_active = False
        self.is_paused = False
        self.alarm_active = False

    def fn_pause(self):
        self.is_paused = not self.is_paused
        logger.debug(f"is_paused={self.is_paused}")

    def fn_forward(self, sec: float = 1.0):
        logger.debug(f"sec={sec}")
        t_cur = time.monotonic()
        self.t_start = max(self.t_start - sec, t_cur - self.t_limit)
        self.t_elapsed = t_cur - self.t_start

    def fn_backward(self, sec: float = 1.0):
        t_cur = time.monotonic()
        self.t_start = min(self.t_start + sec, t_cur)
        self.t_elapsed = t_cur - self.t_start

    def t_str(self, sec: int | float) -> str:
        """Time string.

        sec -> "M:SS"
        """
        m, s = divmod(sec, SEC_MIN)
        if m < MIN_HOUR:
            return f"{m:.0f}:{s:02.0f}"

        h, m = divmod(m, MIN_HOUR)
        return f"{h:.0f}:{m:02.0f}:{s:02.0f}"

    def display(self):
        """Display."""
        logger.debug("")
        t_remain = max(self.t_limit - self.t_elapsed, 0)

        # 表示文字列パーツの生成
        self.col["date"].value = f"{time.strftime('%H:%M:%S')}"
        self.col["limit"].value = self.t_str(self.t_limit)
        self.col["elapsed"].value = self.t_str(self.t_elapsed)
        self.col["remain"].value = self.t_str(t_remain)
        self.col["pbar"].value = "-----"  # dummy

        ## col["state"]
        self.col["state"].value = ""
        if self.is_paused:
            self.col["state"].value = "[PAUSE]"

        ## col["rate"]
        t_rate = self.t_elapsed / self.t_limit * 100
        # パーセント表示で、通常は小数点1位まで、100%だけ "100%" にしたい
        self.col["rate"].value = (
            "100%" if (p := round(t_rate, 1)) == 100 else f"{p:.1f}%"
        )

        ## t_rate に応じて色を変更
        self.col["rate"].color = "white"
        if t_rate >= 80:
            self.col["rate"].color = "yellow"
            if t_rate >= 95:
                self.col["rate"].color = "red"

        # 表示項目：優先順
        col_disp = [
            "remain",
            "title",
            "state",
            "limit",
            "pbar",
            "rate",
            "elapsed",
            "date",
        ]
        for c in self.col:
            self.col[c].use = True

        # 行の長さを計算する関数
        def all_len(cols: list[str]) -> int:
            """Calculate length."""
            logger.debug(f"cols={cols}")
            _len = 0
            for c in cols:
                val = self.col[c].value
                if val:
                    _len += len(val) + 1
                logger.debug(f"'{val}' {_len}")
            _len -= 1 if _len > 0 else 0
            logger.debug(f"all_len={_len}")
            return _len

        # 長過ぎる場合、優先度に応じて表示する項目を省略する
        while all_len(col_disp) > self.term.width:
            c_name = col_disp.pop()  # 最低優先度項目抜く
            logger.debug(f"c_name={c_name},c_priority={col_disp}")
            self.col[c_name].use = False

        if not col_disp:
            # 表示する項目がなくなった場合
            click.secho(f"\r{ESQ_EL0}!?", blink=True, nl=False)
            return

        # プログレスバーを表示する場合の処理
        if "pbar" in col_disp:
            # プログレスバーの長さ
            col_disp.remove("pbar")
            pbar_len = self.term.width - all_len(col_disp) - 1
            logger.debug(f"pbar_len={pbar_len}")

            # ポーズ中・終了時は、風車を止める
            pbar_stop = self.is_paused or (not self.is_active)

            # プログレスバー生成
            self.col["pbar"].value = self.pbar.get_str(
                self.t_elapsed, bar_len=pbar_len, stop=pbar_stop
            )

        # 表示する文字列を作成(スタイル付き)
        # **注意** col_priorityを使うと順番が崩れる
        str_disp = "\r"
        for col_key in self.col:
            c = self.col[col_key]
            if c.use:
                str_disp += click.style(
                    c.value,
                    fg=c.color,
                    bold=c.bold,
                    blink=(c.blink and self.is_paused),
                )
                if c.value:
                    str_disp += " "

        # 表示 (行末の " " は表示しない)
        click.echo(f"{ESQ_EL0}{str_disp[:-1]}", nl=False)

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
