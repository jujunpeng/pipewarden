"""Tests for the alerting hooks module."""

import pytest
from unittest.mock import MagicMock
from pipewarden.checks import CheckResult, CheckStatus
from pipewarden.alerts import (
    AlertDispatcher,
    CallbackAlertHandler,
    LogAlertHandler,
)


def make_result(status: CheckStatus, name: str = "test_check") -> CheckResult:
    return CheckResult(name=name, status=status, message=f"status is {status.value}")


class TestLogAlertHandler:
    def test_send_prints_on_failure(self, capsys):
        handler = LogAlertHandler()
        result = make_result(CheckStatus.FAILED)
        handler.send(result)
        captured = capsys.readouterr()
        assert "[ALERT]" in captured.out
        assert "test_check" in captured.out

    def test_send_prints_on_error(self, capsys):
        handler = LogAlertHandler()
        result = make_result(CheckStatus.ERROR)
        handler.send(result)
        captured = capsys.readouterr()
        assert "error" in captured.out.lower()

    def test_send_silent_on_passed(self, capsys):
        handler = LogAlertHandler()
        result = make_result(CheckStatus.PASSED)
        handler.send(result)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_custom_prefix(self, capsys):
        handler = LogAlertHandler(prefix="[WARN]")
        result = make_result(CheckStatus.FAILED)
        handler.send(result)
        captured = capsys.readouterr()
        assert "[WARN]" in captured.out


class TestCallbackAlertHandler:
    def test_callback_invoked_on_failure(self):
        cb = MagicMock()
        handler = CallbackAlertHandler(cb)
        result = make_result(CheckStatus.FAILED)
        handler.send(result)
        cb.assert_called_once_with(result)

    def test_callback_not_invoked_on_passed(self):
        cb = MagicMock()
        handler = CallbackAlertHandler(cb)
        result = make_result(CheckStatus.PASSED)
        handler.send(result)
        cb.assert_not_called()

    def test_raises_if_not_callable(self):
        with pytest.raises(TypeError):
            CallbackAlertHandler("not_a_function")


class TestAlertDispatcher:
    def test_register_and_dispatch(self):
        dispatcher = AlertDispatcher()
        cb = MagicMock()
        dispatcher.register(CallbackAlertHandler(cb))
        result = make_result(CheckStatus.FAILED)
        dispatcher.dispatch(result)
        cb.assert_called_once_with(result)

    def test_handler_count(self):
        dispatcher = AlertDispatcher()
        dispatcher.register(LogAlertHandler())
        dispatcher.register(LogAlertHandler())
        assert dispatcher.handler_count == 2

    def test_dispatch_to_multiple_handlers(self):
        dispatcher = AlertDispatcher()
        cb1, cb2 = MagicMock(), MagicMock()
        dispatcher.register(CallbackAlertHandler(cb1))
        dispatcher.register(CallbackAlertHandler(cb2))
        result = make_result(CheckStatus.ERROR)
        dispatcher.dispatch(result)
        cb1.assert_called_once()
        cb2.assert_called_once()

    def test_register_invalid_handler_raises(self):
        dispatcher = AlertDispatcher()
        with pytest.raises(TypeError):
            dispatcher.register(object())
