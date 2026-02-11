#
# (c) 2026 Yoichi Tanibayashi
#
import click
from loguru import logger

from . import SEC_MIN, __version__
from .base_timer import BaseTimer
from .click_utils import click_common_opts
from .mylog import loggerInit
from .utils import TerminalContext


@click.group()
@click_common_opts(__version__)
def cli(ctx, debug):
    """Timer CLI."""
    loggerInit(debug)
    logger.debug(ctx)
    logger.debug(debug)


@click.command()
@click.argument("minutes", type=int, nargs=1)
@click.option(
    "--alarm-count",
    "-c",
    type=int,
    default=999,
    show_default=True,
    help="alarm count",
)
@click.option(
    "--alarm-sec1",
    "--s1",
    type=float,
    default=0.5,
    show_default=True,
    help="alarm sec1",
)
@click.option(
    "--alarm-sec2",
    "--s2",
    type=float,
    default=1.5,
    show_default=True,
    help="alarm sec2",
)
@click_common_opts(__version__)
def timer(ctx, minutes, alarm_count, alarm_sec1, alarm_sec2, debug):
    """Simple Timer."""
    loggerInit(debug)
    logger.debug(f"command='{ctx.command.name}'")
    logger.debug(
        f"minutes={minutes},"
        f"alarm_count={alarm_count},alarm_sec=({alarm_sec1},{alarm_sec2})"
    )

    limit = int(minutes * SEC_MIN)

    with TerminalContext():
        _ = BaseTimer(
            ("Timer", "blue"), limit, (alarm_count, alarm_sec1, alarm_sec2)
        ).main()


cli.add_command(timer)
cli.add_command(timer, name="t")


@click.command()
@click.option(
    "--work-time",
    "-w",
    type=float,
    default=25.0,
    show_default=True,
    help="working time",
)
@click.option(
    "--break-time",
    "-b",
    type=float,
    default=5.0,
    show_default=True,
    help="break time",
)
@click.option(
    "--long-break-time",
    "-l",
    type=float,
    default=15.0,
    show_default=True,
    help="long break time",
)
@click.option(
    "--cycles", "-c", type=int, default=4, show_default=True, help="cycles"
)
@click_common_opts(__version__)
def pomodoro(ctx, work_time, break_time, long_break_time, cycles, debug):
    """Pomodoro Timer."""
    loggerInit(debug)
    logger.debug(f"command='{ctx.command.name}'")
    logger.debug(
        (
            f"work_time={work_time}, "
            f"break_time={break_time}, "
            f"long_break_time={long_break_time}, "
            f"cycles={cycles}"
        )
    )

    work_sec = work_time * SEC_MIN
    break_sec = break_time * SEC_MIN
    long_break_sec = long_break_time * SEC_MIN

    title_work = ("WORK", "cyan")
    title_break = ("SHORT_BREAK", "yellow")
    title_lbreak = ("LONG_BREAK", "red")

    tmr = None

    click.echo("[?] for help")

    with TerminalContext():
        while True:
            for i in range(cycles):
                # WORK
                tmr = BaseTimer(title_work, work_sec, enable_next=True)
                if tmr.main():
                    break

                logger.debug(f"i={i}")
                if i < cycles - 1:
                    # SHORT_BREAK
                    tmr = BaseTimer(title_break, break_sec, enable_next=True)
                    if tmr.main():
                        break
                else:
                    # LONG_BREAK
                    tmr = BaseTimer(
                        title_lbreak, long_break_sec, enable_next=True
                    )
                    if tmr.main():
                        break
            else:  # for内部が最後までbreak せずに回りきったとき
                continue
            break  # for内部でbreakされたとき


cli.add_command(pomodoro)
cli.add_command(pomodoro, name="p")
