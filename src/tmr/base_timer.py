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

    IN_KEY_TIMEOUT = 0.1  # sec

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

        self.title = title[0]
        self.title_color = title[1]
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

        self.cmd: list = [
            {
                "info": "pause timer.",
                "keys": [" ", "KEY_ENTER"],
                "fn": self.fn_pause,
            },
            {
                "info": "forward 1 second.",
                "keys": ["+", "=", "KEY_RIGHT", "KEY_CTRL_F"],
                "fn": lambda: self.fn_forward(1.0),
            },
            {
                "info": "backward 1 second.",
                "keys": ["-", "_", "KEY_LEFT", "KEY_CTRL_B"],
                "fn": lambda: self.fn_backward(1.0),
            },
            {
                "info": "foward 10 seconds.",
                "keys": ["KEY_DOWN", "KEY_CTRL_N"],
                "fn": lambda: self.fn_forward(10.0),
            },
            {
                "info": "backward 10 seconds.",
                "keys": ["KEY_UP", "KEY_CTRL_P"],
                "fn": lambda: self.fn_backward(10.0),
            },
            {
                "info": "clear terminal.",
                "keys": ["KEY_CTRL_L"],
                "fn": click.clear,
            },
            {
                "info": "quit.",
                "keys": ["q", "Q", "KEY_ESCAPE"],
                "fn": self.fn_quit,
            },
        ]

        # self.cmd を {"key": fn} の形式に展開する。
        # fn = self.key_map["key"] となる。
        self.key_map = {
            k: item["fn"] for item in self.cmd for k in item["keys"]
        }

    def main(self):
        """Main."""
        logger.debug("start.")

        self.t_start = time.monotonic()
        self.t_elapsed = 0.0

        self.is_active = True
        self.is_paused = False

        with self.term.cbreak():
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

        sec -> "mm:ss"
        """
        m, s = divmod(sec, SEC_MIN)
        if m < MIN_HOUR:
            return f"{m:.0f}:{s:02.0f}"

        h, m = divmod(m, MIN_HOUR)
        return f"{h:.0f}:{m:02.0f}:{s:02.0f}"

    def display(self):
        """Display."""
        t_remain = max(self.t_limit - self.t_elapsed, 0)

        # 表示文字列パートの生成
        str_date = f"{time.strftime('%H:%M:%S')}"
        str_limit = self.t_str(self.t_limit)
        str_elapsed = self.t_str(self.t_elapsed)
        str_remain = self.t_str(t_remain)
        str_state = ""
        if self.is_paused:
            str_state = "[PAUSE] "

        t_rate = self.t_elapsed / self.t_limit * 100
        # パーセント表示で、通常は小数点1位まで、100%だけ "100%" にしたい
        str_rate = "100%" if (p := round(t_rate, 1)) == 100 else f"{p:.1f}%"
        rate_color = "white"
        if t_rate >= 80:
            rate_color = "yellow"
            if t_rate >= 95:
                rate_color = "red"

        # プログレスバーの長さを求める
        str_list = [
            self.title,
            str_date,
            str_limit,
            str_elapsed,
            str_remain,
            str_rate,
            str_state,
        ]
        all_str_len = sum([len(s) for s in str_list])
        sbar_len = self.term.width - all_str_len - len(str_list) - 1

        # ポーズ中、または、終了時は、風車を止める
        sbar_stop = self.is_paused or (not self.is_active)
        str_sbar = self.pbar.get_str(
            self.t_elapsed, bar_len=sbar_len, stop=sbar_stop
        )

        # 表示する文字列を作成(スタイル付き)
        str_disp = "\r"
        str_disp += str_date
        str_disp += " "
        str_disp += click.style(self.title, fg=self.title_color, bold=True)
        str_disp += " "
        str_disp += click.style(str_limit, bold=True)
        str_disp += " "
        if str_state:
            str_disp += click.style(str_state, blink=self.is_paused)
        str_disp += click.style(str_rate, fg=rate_color, blink=self.is_paused)
        str_disp += " "
        str_disp += click.style(
            str_elapsed, fg=rate_color, blink=self.is_paused
        )
        str_disp += " "
        str_disp += click.style(str_sbar, fg=rate_color, blink=self.is_paused)
        str_disp += " "
        str_disp += click.style(
            str_remain, fg=rate_color, blink=self.is_paused
        )

        # 表示
        click.echo(str_disp, nl=False)

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
