#
# (c) 2026 Yoichi Tanibayashi
#
import sys

import click
from loguru import logger

from . import LOG_FMT, __version__, click_common_opts, logLevel
from .base_timer import BaseTimer


@click.group()
@click_common_opts(__version__)
def cli(ctx, debug):
    """Cli."""
    logger.remove()
    logger.add(sys.stderr, format=LOG_FMT, level=logLevel(debug))

    logger.debug(ctx)
    logger.debug(debug)


@click.command()
@click.option(
    "--setting-time",
    "-t",
    type=float,
    default=3.0,
    show_default=True,
    help="setting time",
)
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
def timer(ctx, setting_time, alarm_count, alarm_sec1, alarm_sec2, debug):
    """Simple Timer."""
    logger.remove()
    logger.add(sys.stderr, format=LOG_FMT, level=logLevel(debug))

    logger.debug(f"command='{ctx.command.name}'")
    logger.debug(
        f"setting_time={setting_time},"
        f"alarm_count={alarm_count},alarm_sec=({alarm_sec1},{alarm_sec2})"
    )

    timer = None
    try:
        timer = BaseTimer(
            setting_time,
            prefix=("Timer", "blue"),
            msg="Press any key to stop alarm .. ",
            alarm_params=(alarm_count, alarm_sec1, alarm_sec2),
        )
        timer.main()

    except KeyboardInterrupt as e:
        click.echo()
        logger.warning(type(e).__name__)

    except Exception as e:
        logger.error(f"{type(e).__name__}: {e}")


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
    logger.remove()
    logger.add(sys.stderr, format=LOG_FMT, level=logLevel(debug))

    logger.debug(f"command='{ctx.command.name}'")
    logger.debug(
        (
            f"work_time={work_time}, "
            f"break_time={break_time}, "
            f"long_break_time={long_break_time}, "
            f"cycles={cycles}"
        )
    )

    try:
        while True:
            for _ in range(cycles - 1):
                BaseTimer(work_time, prefix=(f"{'WORK':<10}", "green")).main()

                timer = BaseTimer(
                    break_time, prefix=(f"{'BREAK':<10}", "red")
                )
                timer.main()

            timer = BaseTimer(work_time, prefix=(f"{'WORK':<10}", "green"))
            timer.main()

            timer = BaseTimer(
                long_break_time, prefix=(f"{'LONG BREAK':<10}", "red")
            )
            timer.main()

    except KeyboardInterrupt as e:
        click.echo()
        logger.warning(type(e).__name__)

    except Exception as e:
        logger.error(f"{type(e).__name__}: {e}")

    finally:
        click.echo("End.")


cli.add_command(pomodoro)
cli.add_command(pomodoro, name="p")
