#
# (c) 2026 Yoichi Tanibayashi
#
import shutil
import subprocess
import time
from enum import Enum, auto

import click
from loguru import logger
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.text import Text


class SessionType(Enum):
    """Session Type."""

    WORK = auto()
    BREAK = auto()
    LONG_BREAK = auto()


class App:
    """App."""

    SECs_PER_MIN = 60

    def __init__(
        self,
        work_time: int,
        break_time: int,
        long_break_time: int,
        cycles: int,
    ):
        logger.debug(
            (
                f"work_time={work_time}, "
                f"break_time={break_time}, "
                f"long_break_time={long_break_time}, "
                f"cycles={cycles}"
            )
        )

        self.work_time = work_time
        self.break_time = break_time
        self.long_break_time = long_break_time
        self.cycles = cycles

        self.cur_cycle = 0
        self.current_session_type = SessionType.WORK
        self.remaining_seconds = 0

        self.is_running = True

    def main(self):
        """Main."""
        logger.debug("")

        console = Console()

        # Progress Bar
        self.progress = Progress(
            SpinnerColumn(),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            expand=True,
        )
        self.task_id = self.progress.add_task("", total=100)

        # Layout
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3), Layout(name="body", ratio=1)
        )

        self.time_start = time.time()

        # We start Live context here.
        # Note: click.pause() might break the TUI layout if called inside Live context without pausing it.
        # So we should stop Live context before waiting for user input.

        while self.is_running:
            with Live(layout, console=console, refresh_per_second=10):
                logger.debug(f"cycle: {self.cur_cycle + 1}/{self.cycles}")

                # Define session parameters
                if self.cur_cycle < self.cycles - 1:
                    break_duration = self.break_time
                    break_type = SessionType.BREAK
                else:
                    break_duration = self.long_break_time
                    break_type = SessionType.LONG_BREAK

                # 1. Work Session
                self.current_session_type = SessionType.WORK
                self.update_header(layout)
                for remaining, total_sec in self.cycle_generator(
                    self.cur_cycle, self.work_time
                ):
                    self.update_ui(
                        layout, remaining, total_sec, "Working...", "red"
                    )

            # End of Work Session
            self.notify(
                "Pomodoro", "Work session finished! Time for a break."
            )
            self.wait_for_user()

            # 2. Break Session
            with Live(layout, console=console, refresh_per_second=10):
                self.current_session_type = break_type
                self.update_header(layout)
                for remaining, total_sec in self.cycle_generator(
                    self.cur_cycle, break_duration
                ):
                    self.update_ui(
                        layout, remaining, total_sec, "Break Time", "green"
                    )

            # End of Break Session
            self.notify("Pomodoro", "Break finished! Back to work.")
            self.wait_for_user()

            self.cur_cycle = (self.cur_cycle + 1) % self.cycles

    def update_header(self, layout):
        cycle_text = f"Cycle: {self.cur_cycle + 1}/{self.cycles}"
        session_text = self.current_session_type.name.replace("_", " ")
        header_content = Text(
            f"{cycle_text} | {session_text}",
            justify="center",
            style="bold white",
        )
        layout["header"].update(Panel(header_content, style="blue"))

    def update_ui(self, layout, remaining, total_sec, description, color):
        completed = total_sec - remaining
        self.progress.update(
            self.task_id,
            completed=completed,
            total=total_sec,
            description=description,
        )

        # Update body with progress bar in a panel with dynamic color
        layout["body"].update(
            Panel(self.progress, title=description, border_style=color)
        )

    def notify(self, title, message):
        """Send desktop notification."""
        if shutil.which("notify-send"):
            try:
                subprocess.run(["notify-send", title, message], check=False)
            except Exception as e:
                logger.warning(f"Failed to send notification: {e}")
        else:
            print("\a")

    def wait_for_user(self):
        """Wait for user input."""
        click.pause(info="Press any key to start next session ...")

    def end(self):
        """End."""
        logger.debug("")

    def cycle_generator(self, cycle: int, duration_minutes: int):
        """Cycle Generator."""
        logger.debug(
            f"cycle={cycle}, duration={duration_minutes}, type={self.current_session_type}"
        )

        cycle_start = time.time()
        duration_sec = duration_minutes * self.SECs_PER_MIN
        cycle_end = cycle_start + duration_sec

        while True:
            now = time.time()
            self.remaining_seconds = int(cycle_end - now)

            yield self.remaining_seconds, duration_sec

            if self.remaining_seconds <= 0:
                self.remaining_seconds = 0
                break

            time.sleep(0.1)
