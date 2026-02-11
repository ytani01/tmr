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

from . import ESQ_EL2, MIN_HOUR, SEC_MIN
from .progress_bar import ProgressBar


@dataclass
class TimerCol:
    """Timer column."""

    value: str = ""
    color: str = "white"
    rate_color: bool = False
    bold: bool = False
    use: bool = True
    pause_blink: bool = False


@dataclass
class TimerCmd:
    """Timer Command."""

    name: str
    info: str
    keys: list[str]
    fn: Callable[[], None]  # []:引数なし、 None:戻り値なし


class BaseTimer:
    """Base Timer."""

    IN_KEY_TIMEOUT = 0.2  # sec

    DEF_TITLE = ("Timer", "white")
    DEF_LIMIT = 180.0  # seconds
    COUNT_MANY = 999
    DEF_SEC1 = 0.5
    DEF_SEC2 = 1.5

    PERCENT_COLOR = {
        "white": 0,
        "yellow": 80,
        "red": 95,
    }

    PBAR_LEN_MIN = 10

    type AlarmParams = tuple[int, float, float]

    def __init__(
        self,
        title: tuple[str, str] = DEF_TITLE,
        t_limit: float = DEF_LIMIT,
        alarm_params: AlarmParams = (
            COUNT_MANY,
            DEF_SEC1,
            DEF_SEC2,
        ),
        enable_next: bool = False,
    ):
        """Constractor."""
        logger.debug(
            f"title={title},limit={t_limit},alarm_params={alarm_params}"
        )

        self.col: dict = self.col_list()

        self.col["title"].value = title[0]
        self.col["title"].color = title[1]
        self.t_limit = t_limit
        self.alarm_params = alarm_params
        self.enable_next = enable_next

        self.t_start = 0.0
        self.t_elapsed = 0.0

        self.is_active = False
        self.is_paused = False
        self.alarm_active = False
        self.quit_by_quitcmd = False  # quitコマンドによる終了

        self.pbar = ProgressBar(self.t_limit)

        self.term = Terminal()
        logger.debug(f"term size:{self.term.width}x{self.term.height}")

        self.cmd: List[TimerCmd] = self.cmd_list()
        # self.cmd を {"key": fn} の形式に展開する。
        # fn = self.key_map["key"] となる。
        self.key_map = {k: item.fn for item in self.cmd for k in item.keys}

    def col_list(self) -> dict[str, TimerCol]:
        """Column list."""
        logger.debug("")
        return {  # **重要**: 表示順にすること。TBD:明示的にソートの必要性
            "date": TimerCol(),
            "time": TimerCol(),
            "title": TimerCol(bold=True),
            "limit": TimerCol(),
            "state": TimerCol(rate_color=True, pause_blink=True),
            "rate": TimerCol(rate_color=True, pause_blink=True),
            "elapsed": TimerCol(rate_color=True, pause_blink=True),
            "pbar": TimerCol(rate_color=True, pause_blink=True),
            "remain": TimerCol(rate_color=True, pause_blink=True),
        }

    def cmd_list(self) -> List[TimerCmd]:
        """Get command list as dataclass instances."""
        logger.debug("")
        return [
            TimerCmd(
                name="pause",
                info="Pause timer.",
                keys=["p", "P", " "],
                fn=self.fn_pause,
            ),
            TimerCmd(
                name="forward1",
                info="Forward 1 second.",
                keys=["+", "=", "KEY_RIGHT", "KEY_CTRL_F"],
                fn=lambda: self.fn_forward(1.0),
            ),
            TimerCmd(
                name="backward1",
                info="Backward 1 second.",
                keys=["-", "_", "KEY_LEFT", "KEY_CTRL_B"],
                fn=lambda: self.fn_backward(1.0),
            ),
            TimerCmd(
                name="forward10",
                info="Forward 10 seconds.",
                keys=["KEY_DOWN", "KEY_CTRL_N"],
                fn=lambda: self.fn_forward(10.0),
            ),
            TimerCmd(
                name="bk10",
                info="Backward 10 seconds.",
                keys=["KEY_UP", "KEY_CTRL_P"],
                fn=lambda: self.fn_backward(10.0),
            ),
            TimerCmd(
                name="clear",
                info="Clear terminal.",
                keys=["KEY_CTRL_L"],
                fn=click.clear,
            ),
            TimerCmd(
                name="next",
                info="Next.",
                keys=["n", "N", "KEY_ENTER"],
                fn=self.fn_next,
            ),
            TimerCmd(
                name="quit",
                info="Quit.",
                keys=["q", "Q", "KEY_ESCAPE"],
                fn=self.fn_quit,
            ),
            TimerCmd(
                name="help",
                info="Help.",
                keys=["h", "H", "?"],
                fn=self.fn_help,
            ),
        ]

    def keys_str(self, key_list: list[str]) -> str:
        """Keys string."""
        ret_str = ""
        for k in key_list:
            k_str = f"[{k}]"
            if k == " ":
                k_str = "[SPACE]"
            if k.startswith("KEY_"):
                k_str = f"[{k[4:]}]"
            ret_str += k_str + ", "
        return ret_str[:-2]

    def mk_cmd_str(self, cmd: TimerCmd):
        """Make command str."""
        ret = f"{self.keys_str(cmd.keys):<30}: {cmd.info}"
        return ret

    def main(self) -> bool:
        """Main.

        Return:
            bool: quitコマンドで終了した場合は True
        """
        logger.debug("start.")

        self.t_start = time.monotonic()
        self.t_elapsed = 0.0

        self.is_active = True
        self.is_paused = False

        with self.term.cbreak():
            # メインループ
            while self.is_active:
                # if self.term.width != prev_term_width:
                #     logger.debug(f"term.width={self.term.width}")
                #     prev_term_width = self.term.width
                #     click.echo(f"{ESQ_EL2}")

                # キー入力
                key_name = self.get_key_name()
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

        # タイマー満了、または、終了
        click.echo()

        if (
            thr := self.ring_alarm()
        ):  # アラーム alarm_active によっては鳴らない
            try:
                # click.secho(
                #     "[Press any key]\r", bold=True, blink=True, nl=False
                # )

                with self.term.cbreak():
                    while self.alarm_active:
                        key_name = self.get_key_name()
                        if not key_name:
                            continue

                        if self.key_map.get(key_name) == self.fn_quit:
                            self.quit_by_quitcmd = True
                        logger.debug(f"in_key={key_name!r}")
                        click.echo(f"{ESQ_EL2}{key_name!r}\r", nl=False)
                        break
            finally:
                self.alarm_active = False
                thr.join()
                click.echo(f"{ESQ_EL2}\r", nl=False)

        logger.debug("done.")
        return self.quit_by_quitcmd

    def get_key_name(self) -> str:
        """Get key name.

        **Important**
        Remember to call self.term.break() before calling this function.
        """
        in_key = self.term.inkey(timeout=self.IN_KEY_TIMEOUT)

        if not in_key:
            return ""

        logger.debug(
            f"Raw: {in_key!r}, Code: {in_key.code}, Name: {in_key.name}"
        )

        key_name = ""
        if in_key.name:
            key_name = in_key.name
        else:
            key_name = str(in_key)
        logger.debug(f"key_name='{key_name}'")

        return key_name

    def fn_help(self):
        """Quit."""
        logger.debug("")
        click.echo(f"{ESQ_EL2}COMMAND LIST:")
        for c in self.cmd:
            if c.name == "next" and not self.enable_next:
                continue
            click.echo(f"  {self.mk_cmd_str(c)}")
        click.echo()

    def fn_quit(self):
        """Quit."""
        logger.debug("")
        self.is_active = False
        self.is_paused = False
        self.alarm_active = False
        self.quit_by_quitcmd = True

    def fn_next(self):
        """Quit and next."""
        logger.debug("")
        if not self.enable_next:
            return

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

    def display(self):
        """Display."""
        # logger.debug("")
        t_remain = max(self.t_limit - self.t_elapsed, 0)

        # 表示文字列パーツの生成
        def t_str(sec: int | float) -> str:
            """Time string.

            sec -> "M:SS"
            """
            m, s = divmod(sec, SEC_MIN)
            if m < MIN_HOUR:
                return f"{m:.0f}:{s:02.0f}"

            h, m = divmod(m, MIN_HOUR)
            return f"{h:.0f}:{m:02.0f}:{s:02.0f}"

        self.col["date"].value = f"{time.strftime('%Y-%m-%d')}"
        self.col["time"].value = f"{time.strftime('%H:%M:%S')}"
        self.col["limit"].value = t_str(self.t_limit)
        self.col["elapsed"].value = t_str(self.t_elapsed)
        self.col["remain"].value = t_str(t_remain)
        self.col["pbar"].value = "-" * self.PBAR_LEN_MIN  # 仮の値

        ## col["state"]
        self.col["state"].value = ""
        if self.is_paused:
            self.col["state"].value = "[PAUSE]"
        if self.t_elapsed >= self.t_limit:
            self.col["state"].value = "[TIME UP]"

        ## col["rate"]
        t_rate = self.t_elapsed / self.t_limit * 100
        # パーセント表示で、通常は小数点1位まで、100%だけ "100%" にしたい
        self.col["rate"].value = (
            "(100%)" if (p := round(t_rate, 1)) == 100 else f"({p:.1f}%)"
        )

        ## t_rate に応じて色を変更
        for c in self.col:
            col = self.col[c]
            if not col.rate_color:
                continue

            for c in self.PERCENT_COLOR:
                if t_rate >= self.PERCENT_COLOR[c]:
                    col.color = c

        # 表示項目：優先順
        col_disp = [
            "remain",
            "title",
            "state",
            "pbar",
            "limit",
            "rate",
            "elapsed",
            "time",
            "date",
        ]
        for c in self.col:
            self.col[c].use = True

        # 行の長さを計算する関数
        def all_len(cols: list[str]) -> int:
            """Calculate length."""
            # logger.debug(f"cols={cols}")
            _len = 0
            for c in cols:
                val = self.col[c].value
                if val:
                    _len += len(val) + 1
                # logger.debug(f"'{val}' {_len}")
            _len -= 1 if _len > 0 else 0
            # logger.debug(f"all_len={_len}")
            return _len

        # 長過ぎる場合、優先度に応じて表示する項目を省略する
        while all_len(col_disp) > self.term.width:
            c_name = col_disp.pop()  # 最低優先度項目抜く
            # logger.debug(f"c_name={c_name},c_priority={col_disp}")
            self.col[c_name].use = False

        if not col_disp:
            # 表示する項目がなくなった場合
            click.secho(f"\r{ESQ_EL2}!?", blink=True, nl=False)
            return

        # プログレスバーを表示する場合の処理
        if "pbar" in col_disp:
            # プログレスバーの長さ
            col_disp.remove("pbar")
            pbar_len = self.term.width - all_len(col_disp) - 1
            # logger.debug(f"pbar_len={pbar_len}")

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
            f_blink = False
            c = self.col[col_key]
            if c.use:
                if c.pause_blink and self.is_paused:
                    f_blink = True
                if col_key == "state" and self.t_elapsed >= self.t_limit:
                    f_blink = True

                str_disp += click.style(
                    c.value,
                    fg=c.color,
                    bold=c.bold,
                    blink=f_blink,
                )
                if c.value:
                    str_disp += " "

        # 表示 ([:-1] .. 行末の " " は表示しない)
        click.echo(f"{ESQ_EL2}{str_disp[:-1]}", nl=False)

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

    def ring_alarm(self) -> threading.Thread | None:
        """Ring alarm.

        make thread and start.
        """
        logger.debug(f"alarm_params={self.alarm_params}")

        if not self.alarm_active:
            return None

        thr = threading.Thread(
            target=self.thr_alarm, args=self.alarm_params, daemon=True
        )
        thr.start()
        return thr
