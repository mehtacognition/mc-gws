from unittest.mock import patch, MagicMock
from mcgws.notify import send_imessage, notify_error


def test_send_imessage_success():
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        send_imessage("+15551234567", "Test message")


def test_send_imessage_failure():
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "Connection failed"

    with patch("subprocess.run", return_value=mock_result):
        import pytest
        with pytest.raises(RuntimeError, match="Failed to send"):
            send_imessage("+15551234567", "Test message")


def test_send_imessage_escapes_quotes():
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        send_imessage("+15551234567", 'He said "hello"')

    call_args = mock_run.call_args[0][0]
    script = call_args[call_args.index("-e") + 1]
    assert '\\"hello\\"' in script


def test_notify_error_sends_to_phone():
    config = {"self_reminder_phone": "+15551234567"}

    with patch("mcgws.notify.send_imessage") as mock_send:
        notify_error(config, "Something broke")

    mock_send.assert_called_once_with("+15551234567", "Something broke")


def test_notify_error_no_phone_configured():
    config = {}

    with patch("mcgws.notify.send_imessage") as mock_send:
        notify_error(config, "Something broke")

    mock_send.assert_not_called()


def test_notify_error_swallows_exceptions():
    config = {"self_reminder_phone": "+15551234567"}

    with patch("mcgws.notify.send_imessage", side_effect=RuntimeError("fail")):
        # Should not raise
        notify_error(config, "Something broke")
