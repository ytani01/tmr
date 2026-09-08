#
# (c) 2026 Yoichi Tanibayashi
#
import math
import os
import signal
import subprocess
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

import click
from blessed import Terminal

from .clock import TimerClock
from .mylog import getLogger
from .terminal import ESQ_EL2
from .timefmt import SEC_DAY
from .view import TimerTitle, TimerView

MAX_ALARM_SEC = SEC_DAY  # time.sleep() が OverflowError にならない上限


@dataclass(frozen=True)
class AlarmParams:
    """Alarm parameters.

    ``cmd`` を指定すると、ビープの代わりにそのコマンドを
    シェル経由で 1 回だけ実行する。
    """

    count: int
    sec1: float
    sec2: float
    cmd: str | None = None

    def __post_init__(self) -> None:
        """各フィールドの妥当性を確認する。"""
        if self.cmd is not None and not self.cmd.strip():
            raise ValueError(f"cmd must not be empty: cmd={self.cmd!r}")

        if self.count < 0:
            raise ValueError(f"count must be >= 0: count={self.count}")

        for name in ("sec1", "sec2"):
            value = getattr(self, name)
            if not math.isfinite(value) or value < 0 or value > MAX_ALARM_SEC:
                raise ValueError(
                    f"{name} must be a finite number in "
                    f"[0, {MAX_ALARM_SEC}]: {name}={value}"
                )


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
    ALARM_STOP_SEC = 1.0  # コマンドを止めるときに待つ秒数
    LOG_MAX_LEN = 200  # コマンドの出力をログに出す長さの上限

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

        # アラームのコマンド（thr_alarm が入れ、stop_alarm_cmd が止める）
        self.alarm_thr: threading.Thread | None = None
        self.alarm_proc: subprocess.Popen[str] | None = None
        # 起動を試みたら（失敗しても）立てる。stop_alarm_cmd がこれを待つ
        self.alarm_proc_ready = threading.Event()
        self.alarm_cmd_stopped = False  # キー入力で止めたか

        self.term = Terminal()
        self.__log.debug(f"term size:{self.term.width}x{self.term.height}")

        self.view = TimerView(self.term, title)

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

        ``Ctrl-C`` で抜けるときも、アラームのコマンドを止めてから
        送出し直す。``start_new_session=True`` で子は別セッションに
        いるので、端末が送る ``SIGINT`` は子に届かない
        （握り潰す ``TerminalContext`` へ渡す前に、ここで止める）。
        後始末の最中の 2 度目の ``Ctrl-C`` は無視する
        （``SIGKILL`` を送る前に抜けると、子が残るため）。

        Return:
            bool: quitコマンドで終了した場合は True
        """
        try:
            return self._main()

        except KeyboardInterrupt:
            self.__log.debug("KeyboardInterrupt")
            self.cleanup_by_interrupt()
            raise

    def cleanup_by_interrupt(self) -> None:
        """``Ctrl-C`` で抜けるときの後始末。

        後始末には最大 3 秒かかるので、その間に「効かない」と思った
        利用者が 2 度目の ``Ctrl-C`` を押しうる。そこで抜けると
        ``SIGKILL`` を送る前に終わってしまい、``SIGTERM`` を無視する
        コマンドが残る。**後始末の間だけ ``SIGINT`` を止めておく**
        （``pthread_sigmask`` は POSIX のみだが、``killpg`` を
        使っている時点で POSIX 前提）。
        """
        if self.alarm_thr is None:
            return

        # 解除ではなく、元のマスクに戻す。呼ぶ側が SIGINT を
        # 止めていることがあるため（ライブラリとして使う経路）
        old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
        try:
            _ = self.stop_alarm_cmd(self.alarm_thr)
        except KeyboardInterrupt:
            # 止める前に届いていた分。後始末は済ませる
            self.__log.debug("KeyboardInterrupt (again)")
        finally:
            _ = signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)

    def _main(self) -> bool:
        """メインループ本体（``main()`` から呼ぶ）。"""
        self.__log.debug("start.")

        # 同じインスタンスで 2 回目を回せるように、毎回初期化する
        self.alarm_proc = None
        self.alarm_proc_ready.clear()
        self.alarm_cmd_stopped = False
        self.alarm_thr = None

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
            self.alarm_thr = thr  # KeyboardInterrupt のときの後始末用
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

        if thr and self.stop_alarm_cmd(thr):
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

    def exec_alarm_cmd(self, cmd: str) -> None:
        """アラームのコマンドをシェル経由で 1 回だけ実行する。

        端末を子プロセスと取り合わないよう、``stdin`` は捨て、
        ``stdout`` / ``stderr`` は取り込んでログに回す
        （画面に直接書かせない）。

        失敗しても（コマンドが無い、非ゼロ終了）ログに残して続行し、
        ビープにフォールバックはしない。
        """
        self.__log.debug(f"cmd={cmd!r}")

        try:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace",
                # 新しいセッションにして、止めるときに
                # プロセスグループごと落とせるようにする
                start_new_session=True,
            )
        except OSError as e:
            self.__log.error(f"cmd={cmd!r}: {e!r}")
            self.alarm_proc_ready.set()
            return

        self.alarm_proc = proc
        self.alarm_proc_ready.set()

        out, err = proc.communicate()  # 終わる（or 止められる）まで待つ

        for name, text in (("stdout", out), ("stderr", err)):
            if text and text.strip():
                # 出力が長いコマンドでログを埋めない
                self.__log.debug(
                    f"{name}: {text.strip()[: self.LOG_MAX_LEN]}"
                )

        if proc.returncode == 0 or self.alarm_cmd_stopped:
            # 自分で止めたときの負の returncode は失敗ではない
            self.__log.debug(f"cmd={cmd!r}: returncode={proc.returncode}")
        else:
            self.__log.warning(f"cmd={cmd!r}: returncode={proc.returncode}")

    def kill_alarm_cmd(
        self, proc: subprocess.Popen[str], sig: int, name: str
    ) -> bool:
        """コマンドのプロセスグループごとシグナルを送る。

        ``shell=True`` なのでシグナルの相手はシェルになる。シェルが
        ``sleep`` などを子として持っていると、シェルだけ落としても
        孫が残り、``stdout`` のパイプを握ったままになる。
        ``start_new_session=True`` にしてあるので、プロセスグループ
        （id はシェルの pid）ごと落とす。

        ``Popen.send_signal()`` を使わないのは、それがシェル 1 つにしか
        届かないため。代わりに、``send_signal()`` がやっている
        「終わった相手には送らない」確認（pid が再利用され、無関係な
        プロセスグループを撃つのを防ぐ）を、ここで自分で行う。

        Returns:
            bool: 送れた（または既に居ない）なら True
        """
        if proc.poll() is not None:
            # 既に終わって回収済み。この pid は再利用されうる
            self.__log.debug(f"{name}: already done: pid={proc.pid}")
            return True

        self.__log.debug(f"{name}: pid={proc.pid}")

        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            self.__log.debug(f"{name}: already gone: pid={proc.pid}")
        except OSError as e:
            self.__log.error(f"{name}: {e!r}")
            return False

        return True

    def stop_alarm_cmd(self, thr: threading.Thread) -> bool:
        """実行中のアラームのコマンドを止める。

        キー入力でアラームを抜けたときに呼ぶ。止めないと、コマンドが
        終わるまで ``main()`` が返らず「[Q] が効かない」ように見える。

        ``SIGTERM`` で止まらなければ、少し待ってから ``SIGKILL``。

        Args:
            thr: アラームのスレッド。コマンドの終了待ちに使う

        Returns:
            bool: 呼び出し元が ``thr.join()`` してよいなら True
                （False なら、待つと固まる恐れがある）
        """
        if self.alarm_params.cmd is not None:
            # スレッドがコマンドを起動し終えるのを待つ
            # （待たないと、止めそこねたまま join() で固まる）
            self.alarm_proc_ready.wait(timeout=self.ALARM_STOP_SEC)

        proc = self.alarm_proc
        if proc is None or proc.poll() is not None:
            # ビープの経路、起動に失敗、または自然に終わっている
            return True

        self.alarm_cmd_stopped = True

        for sig, name in (
            (signal.SIGTERM, "SIGTERM"),
            (signal.SIGKILL, "SIGKILL"),
        ):
            if not self.kill_alarm_cmd(proc, sig, name):
                return False

            thr.join(timeout=self.ALARM_STOP_SEC)
            if not thr.is_alive():
                return True

        self.__log.warning(f"cmd not stopped: pid={proc.pid}")
        return False

    def thr_alarm(self, params: AlarmParams) -> None:
        """Alarm thread function."""
        self.__log.debug(f"params={params}")

        if params.cmd is not None:
            # ビープの代わりにコマンドを 1 回だけ実行する。
            # コマンドが自然に終わってもキー入力は待つので、
            # alarm_active は False にしない。
            self.exec_alarm_cmd(params.cmd)
            return

        for _ in range(params.count):
            for s in [params.sec1, params.sec2]:
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
            args=(self.alarm_params,),
            daemon=True,
        )

        # SIGINT を止めてから起動する。スレッドは生成時のマスクを
        # 継ぐので、こうしないと Ctrl-C をこのスレッドが受け取り、
        # 後始末の最中でもメインスレッドへ KeyboardInterrupt が飛ぶ
        # （cleanup_by_interrupt() のマスクが効かなくなる）。
        old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
        try:
            thr.start()
        finally:
            _ = signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)

        return thr
