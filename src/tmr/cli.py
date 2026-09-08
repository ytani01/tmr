#
# (c) 2026 Yoichi Tanibayashi
#
import math

import click

from . import __version__
from .click_utils import click_common_opts
from .config import ConfigGroup
from .mylog import getLogger, loggerInit
from .pomodoro import PomodoroConfig, PomodoroTimer
from .terminal import TerminalContext
from .timefmt import SEC_DAY, SEC_MIN
from .timer import AlarmParams, Timer
from .view import TimerTitle

_log = getLogger("main")


def _reject_non_finite(ctx, param, value):
    """``nan`` / ``inf`` を弾く（``FloatRange`` の後段用）。

    ``ctx`` / ``param`` は使わないが、``click`` のコールバック規約で
    3 引数を受ける。
    """
    if not math.isfinite(value):
        raise click.BadParameter(f"must be finite: {value}")

    return value


@click.group(cls=ConfigGroup)
@click_common_opts(__version__)
def cli(ctx, debug):
    """Timer CLI."""
    loggerInit(debug)
    _log.debug(ctx)
    _log.debug(debug)
    _log.debug(f"default_map={ctx.default_map}")


@click.command()
@click.argument("minutes", type=click.IntRange(min=1), nargs=1)
@click.option(
    "--title",
    "-t",
    type=str,
    default="Timer",
    show_default=True,
    help="alarm title",
)
@click.option(
    "--title-color",
    "--color",
    "-c",
    type=str,
    default="blue",
    show_default=True,
    help="title color",
)
@click.option(
    "--alarm-count",
    type=click.IntRange(min=0),
    default=999,
    show_default=True,
    help="alarm count",
)
@click.option(
    "--alarm-sec1",
    "--s1",
    type=click.FloatRange(min=0, max=SEC_DAY),
    default=0.5,
    show_default=True,
    callback=_reject_non_finite,
    help="alarm sec1",
)
@click.option(
    "--alarm-sec2",
    "--s2",
    type=click.FloatRange(min=0, max=SEC_DAY),
    default=1.5,
    show_default=True,
    callback=_reject_non_finite,
    help="alarm sec2",
)
@click_common_opts(__version__)
def timer(
    ctx,
    minutes,
    title,
    title_color,
    alarm_count,
    alarm_sec1,
    alarm_sec2,
    debug,
):
    """Simple Timer."""
    loggerInit(debug)
    _log.debug(f"command='{ctx.command.name}'")
    _log.debug(
        f"minutes={minutes},"
        f"title={title!r},title_color={title_color!r},"
        f"alarm_count={alarm_count},alarm_sec=({alarm_sec1},{alarm_sec2})"
    )

    limit = int(minutes * SEC_MIN)

    with TerminalContext():
        _ = Timer(
            TimerTitle(title, title_color),
            limit,
            AlarmParams(alarm_count, alarm_sec1, alarm_sec2),
        ).main()


cli.add_command(timer)
cli.add_command(timer, name="t")


@click.command()
@click.option(
    "--work-time",
    "-w",
    type=click.FloatRange(min=0, min_open=True),
    default=25.0,
    show_default=True,
    callback=_reject_non_finite,
    help="working time",
)
@click.option(
    "--break-time",
    "-b",
    type=click.FloatRange(min=0, min_open=True),
    default=5.0,
    show_default=True,
    callback=_reject_non_finite,
    help="break time",
)
@click.option(
    "--long-break-time",
    "-l",
    type=click.FloatRange(min=0, min_open=True),
    default=15.0,
    show_default=True,
    callback=_reject_non_finite,
    help="long break time",
)
@click.option(
    "--cycles",
    "-c",
    type=click.IntRange(min=1),
    default=4,
    show_default=True,
    help="cycles",
)
@click_common_opts(__version__)
def pomodoro(ctx, work_time, break_time, long_break_time, cycles, debug):
    """Pomodoro Timer."""
    loggerInit(debug)
    _log.debug(f"command='{ctx.command.name}'")
    _log.debug(
        f"work_time={work_time}, "
        f"break_time={break_time}, "
        f"long_break_time={long_break_time}, "
        f"cycles={cycles}"
    )

    # 秒換算
    config = PomodoroConfig(
        work_sec=work_time * SEC_MIN,
        break_sec=break_time * SEC_MIN,
        long_break_sec=long_break_time * SEC_MIN,
        cycles=cycles,
    )

    timer = PomodoroTimer(config)

    click.echo("Start Pomodoro Timer: [?] for help")

    with TerminalContext():
        timer.run()


cli.add_command(pomodoro)
cli.add_command(pomodoro, name="p")
