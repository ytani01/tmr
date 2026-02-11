from unittest import mock

from tmr.utils import ESQ_CSR_OFF, ESQ_CSR_ON, ESQ_EL2, TerminalContext


def test_terminal_context_normal():
    """Verify cursor is hidden on enter and shown on exit"""
    with mock.patch("click.echo") as mock_echo:
        with TerminalContext():
            pass

        # Enter: hide cursor
        mock_echo.assert_any_call(ESQ_CSR_OFF, nl=False)
        # Exit: show cursor
        mock_echo.assert_any_call(f"{ESQ_CSR_ON}", nl=False)


def test_terminal_context_keyboard_interrupt():
    """Verify KeyboardInterrupt is suppressed and cursor is shown"""
    with mock.patch("click.echo") as mock_echo:
        with TerminalContext():
            raise KeyboardInterrupt()

        # Enter: hide cursor
        mock_echo.assert_any_call(ESQ_CSR_OFF, nl=False)  # type: ignore[unreachable]
        # Exit: show cursor
        mock_echo.assert_any_call(f"{ESQ_CSR_ON}", nl=False)
        # Exit: handle interrupt
        mock_echo.assert_any_call(f"\n{ESQ_EL2}Aborted.")


def test_terminal_context_other_exception():
    """Verify other exceptions are NOT suppressed"""
    with mock.patch("click.echo") as mock_echo:
        try:
            with TerminalContext():
                raise ValueError("Test Error")
        except ValueError:
            pass
        else:
            assert False, "ValueError should be raised"  # type: ignore[unreachable]

        # Enter: hide cursor
        mock_echo.assert_any_call(ESQ_CSR_OFF, nl=False)
        # Exit: show cursor (always called in finally)
        mock_echo.assert_any_call(f"{ESQ_CSR_ON}", nl=False)
