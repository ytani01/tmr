#
# (c) 2026 Yoichi Tanibayashi
#
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

import click
from blessed import Terminal

from .clock import TimerClock
from .mylog import getLogger
from .terminal import ESQ_EL2
from .view import TimerTitle, TimerView


@dataclass(frozen=True)
class AlarmParams:
    """Alarm parameters."""

    count: int
    sec1: float
    sec2: float


@dataclass
class TimerCmd:
    """Timer Command."""

    name: str
    info: str
    keys: list[str]
    fn: Callable[[], None]  # []:引数なし、 None:戻り値なし


class Timer:
    """Timer.

    メインループとキー操作・アラームだけの層。
    時刻は `TimerClock`、表示は `TimerView` が持つ。

    Note:
        This class uses `loguru` for logging. It is recommended to initialize
        the logger (e.g., using `tmr.mylog.loggerInit`) before using this class
        to ensure logs are formatted correctly.
    """

    __log = getLogger(__qualname__)

    IN_KEY_TIMEOUT = 0.2  # sec

    DEF_LIMIT = 180.0  # seconds
    COUNT_MANY = 999
    DEF_SEC1 = 0.5
    DEF_SEC2 = 1.5

    DEF_TITLE = TimerTitle("Timer", "white")
    DEF_ALARM = AlarmParams(COUNT_MANY, DEF_SEC1, DEF_SEC2)

    def __init__(
        self,
        title: TimerTitle = DEF_TITLE,
        t_limit: float = DEF_LIMIT,
        alarm_params: AlarmParams = DEF_ALARM,
        enable_next: bool = False,
    ):
        """Constructor."""
        self.__log.debug(
            f"title={title},limit={t_limit},alarm_params={alarm_params}"
        )

        self.alarm_params = alarm_params
        self.enable_next = enable_next

        self.clock = TimerClock(t_limit)

        self.is_active = False
        self.alarm_active = False
        self.quit_by_quitcmd = False  # quitコマンドによる終了

        self.term = Terminal()
        self.__log.debug(f"term size:{self.term.width}x{self.term.height}")

        self.view = TimerView(self.term, t_limit, title)

        self.cmd: list[TimerCmd] = self.cmd_list()
        # self.cmd を {"key": fn} の形式に展開する。
        # fn = self.key_map["key"] となる。
        self.key_map = {k: item.fn for item in self.cmd for k in item.keys}

    def cmd_list(self) -> list[TimerCmd]:
        """Get command list as dataclass instances."""
        self.__log.debug("")
        return [
            TimerCmd(
                name="pause",
                info="Pause timer.",
                keys=["P", " "],
                fn=self.fn_pause,
            ),
            TimerCmd(
                name="backward1",
                info="Backward 1 second.",
                keys=["KEY_LEFT", "KEY_CTRL_B", "H", "-", "KEY_BACKSPACE"],
                fn=lambda: self.fn_backward(1.0),
            ),
            TimerCmd(
                name="forward1",
                info="Forward 1 second.",
                keys=["KEY_RIGHT", "KEY_CTRL_F", "L", "+", "="],
                fn=lambda: self.fn_forward(1.0),
            ),
            TimerCmd(
                name="bk10",
                info="Backward 10 seconds.",
                keys=["KEY_UP", "KEY_CTRL_P", "K"],
                fn=lambda: self.fn_backward(10.0),
            ),
            TimerCmd(
                name="forward10",
                info="Forward 10 seconds.",
                keys=["KEY_DOWN", "KEY_CTRL_N", "J"],
                fn=lambda: self.fn_forward(10.0),
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
                keys=["N", "KEY_ENTER"],
                fn=self.fn_next,
            ),
            TimerCmd(
                name="quit",
                info="Quit.",
                keys=["Q", "KEY_ESCAPE"],
                fn=self.fn_quit,
            ),
            TimerCmd(
                name="help",
                info="Help.",
                keys=["?"],
                fn=self.fn_help,
            ),
        ]

    KEY_WORD_MAP = {
        "KEY": "",
        "CTRL": "[Ctrl]+",
        "SHIFT": "[Shift]+",
        " ": "[SPACE]",
        "RIGHT": "[→]",
        "LEFT": "[←]",
        "UP": "[↑]",
        "DOWN": "[↓]",
    }

    def keys_str(self, key_list: list[str]) -> str:
        """Keys list to string names.

        [CTR_X] --> [Ctrl]+[x]
        [LEFT] --> []
        [KEY_ENTER] --> [ENTER]
        """
        ret_str = ""
        for k in key_list:
            k_str = ""
            for w in k.split("_"):
                if w in self.KEY_WORD_MAP:
                    k_str += self.KEY_WORD_MAP[w]
                    continue
                k_str += f"[{w}]"
            ret_str += k_str + ", "
        return ret_str[:-2]

    def mk_cmd_str(self, cmd: TimerCmd):
        """Make command str."""
        ret = f"{self.keys_str(cmd.keys):<40}: {cmd.info}"
        return ret

    def _display(self) -> None:
        """現在の状態を表示する。"""
        self.view.display(
            self.clock,
            is_active=self.is_active,
            alarm_active=self.alarm_active,
        )

    def main(self) -> bool:
        """Main.

        Return:
            bool: quitコマンドで終了した場合は True
        """
        self.__log.debug("start.")

        self.clock.start()

        self.is_active = True

        with self.term.cbreak():
            # メインループ
            while self.is_active:
                # キー入力
                key_name = self.get_key_name()
                if key_name:
                    self.__log.debug(f"key_name=[{key_name}]")

                # キーマップに登録されているメソッドを呼び出す
                if key_name in self.key_map:
                    self.key_map[key_name]()

                # 時間経過
                self.clock.tick()

                # 表示
                self._display()

                # 終了判定
                if self.clock.is_timeup:
                    if not self.clock.is_paused:
                        self.is_active = False
                        self.alarm_active = True

        # タイマー満了、または、終了
        key_name = ""
        thr = None
        if (
            thr := self.ring_alarm()
        ):  # アラーム alarm_active によっては鳴らない
            with self.term.cbreak():
                while self.alarm_active:
                    key_name = self.get_key_name()
                    if not key_name:
                        self._display()
                        continue
                    self.__log.debug(f"in_key=[{key_name}]")
                    break

        self.alarm_active = False
        self._display()
        click.echo()

        click.echo(f"{ESQ_EL2}{self.keys_str([key_name])}\r", nl=False)

        if self.key_map.get(key_name) == self.fn_quit:
            self.quit_by_quitcmd = True

        if thr:
            thr.join()
        click.echo(f"{ESQ_EL2}\r", nl=False)

        self.__log.debug("done.")
        return self.quit_by_quitcmd

    def get_key_name(self) -> str:
        """Get key name.

        **Important**
        Remember to call self.term.break() before calling this function.
        """
        in_key = self.term.inkey(timeout=self.IN_KEY_TIMEOUT)

        if not in_key:
            return ""

        self.__log.debug(
            f"Raw: {in_key!r}, Code: {in_key.code}, Name: {in_key.name}"
        )

        key_name = ""
        if in_key.name:
            key_name = in_key.name
        else:
            key_name = str(in_key)
            if key_name.islower():
                key_name = key_name.upper()
        self.__log.debug(f"key_name='{key_name}'")

        return key_name

    def fn_help(self):
        """Quit."""
        self.__log.debug("")
        click.echo(f"{ESQ_EL2}COMMAND LIST")
        for c in self.cmd:
            if c.name == "next" and not self.enable_next:
                continue
            click.echo(f"  {self.mk_cmd_str(c)}")
        click.echo()

    def fn_quit(self):
        """Quit."""
        self.__log.debug("")
        self.is_active = False
        self.clock.is_paused = False
        self.alarm_active = False
        self.quit_by_quitcmd = True

    def fn_next(self):
        """Quit and next."""
        self.__log.debug("")
        if not self.enable_next:
            return

        self.is_active = False
        self.clock.is_paused = False
        self.alarm_active = False

    def fn_pause(self):
        """Toggle pause."""
        self.clock.toggle_pause()

    def fn_forward(self, sec: float = 1.0):
        """Forward."""
        self.clock.forward(sec)

    def fn_backward(self, sec: float = 1.0):
        """Backward."""
        self.clock.backward(sec)

    def thr_alarm(self, count, sec1, sec2):
        """Alarm thread function."""
        self.__log.debug(f"count={count},sec1={sec1},sec2={sec2}")

        for _ in range(count):
            for s in [sec1, sec2]:
                if self.alarm_active:
                    click.echo("\a", nl=False)
                    time.sleep(s)

        self.alarm_active = False

    def ring_alarm(self) -> threading.Thread | None:
        """Ring alarm.

        make thread and start.
        """
        self.__log.debug(f"alarm_params={self.alarm_params}")

        if not self.alarm_active:
            return None

        thr = threading.Thread(
            target=self.thr_alarm,
            args=(
                self.alarm_params.count,
                self.alarm_params.sec1,
                self.alarm_params.sec2,
            ),
            daemon=True,
        )
        thr.start()
        return thr
