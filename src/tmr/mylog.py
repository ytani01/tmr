#
# (c) 2026 Yoichi Tanibayashi
#
LOG_FMT = (
    "<level>"
    "<white>{time:MM/DD HH:mm:ss}</white> "
    "{level.icon} {level} "
    "{file}<green>:</green>{line} "
    "{function}()<green>></green> "
    "<white>{message}</white>"
    "</level>"
)


def logLevel(debug=False) -> str:
    """Log level."""
    return "DEBUG" if debug else "INFO"
