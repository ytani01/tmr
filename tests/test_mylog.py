import io

import pytest
from loguru import logger

from tmr import mylog
from tmr.mylog import getLogger, loggerInit


@pytest.fixture(autouse=True)
def _clean_logger():
    """loguru と登録名のグローバル状態をテストごとにリセットする。"""
    yield
    logger.remove()
    mylog._registered_names.clear()


def test_parse_tmr_log():
    assert mylog._parse_tmr_log("BaseTimer=DEBUG,main=INFO") == {
        "BaseTimer": "DEBUG",
        "main": "INFO",
    }


def test_parse_tmr_log_empty():
    assert mylog._parse_tmr_log("") == {}


def test_parse_tmr_log_ignores_malformed_items():
    assert mylog._parse_tmr_log("BaseTimer=DEBUG, ,noequals") == {
        "BaseTimer": "DEBUG"
    }


def test_default_level_is_info(monkeypatch):
    monkeypatch.delenv("TMR_LOG", raising=False)
    out = io.StringIO()
    loggerInit(debug=False, out=out)

    _log = getLogger("Foo")
    _log.debug("debug message")
    _log.info("info message")

    text = out.getvalue()
    assert "debug message" not in text
    assert "info message" in text


def test_debug_flag_enables_debug(monkeypatch):
    monkeypatch.delenv("TMR_LOG", raising=False)
    out = io.StringIO()
    loggerInit(debug=True, out=out)

    _log = getLogger("Foo")
    _log.debug("debug message")

    assert "debug message" in out.getvalue()


def test_unbound_logger_falls_back_to_module_name(monkeypatch):
    monkeypatch.delenv("TMR_LOG", raising=False)
    out = io.StringIO()
    loggerInit(debug=True, out=out)

    logger.debug("plain logger message")

    assert "plain logger message" in out.getvalue()


def test_tmr_log_overrides_level_per_name(monkeypatch):
    monkeypatch.setenv("TMR_LOG", "Loud=DEBUG")
    out = io.StringIO()

    _log_loud = getLogger("Loud")
    _log_quiet = getLogger("Quiet")
    loggerInit(debug=False, out=out)

    _log_loud.debug("loud debug")
    _log_quiet.debug("quiet debug")

    text = out.getvalue()
    assert "loud debug" in text
    assert "quiet debug" not in text


def test_tmr_log_unknown_name_warns(monkeypatch):
    monkeypatch.setenv("TMR_LOG", "GhostModule=DEBUG")
    out = io.StringIO()

    loggerInit(debug=False, out=out)

    assert "GhostModule" in out.getvalue()
    assert "WARNING" in out.getvalue()


def test_tmr_log_known_name_does_not_warn(monkeypatch):
    monkeypatch.setenv("TMR_LOG", "Known=DEBUG")
    out = io.StringIO()

    getLogger("Known")
    loggerInit(debug=False, out=out)

    assert "WARNING" not in out.getvalue()
