"""Integration tests — verify full command flow with mocked backends."""

import json
from unittest.mock import patch, MagicMock
from mcgws.cli import main


def test_cli_help(capsys):
    import sys
    with patch.object(sys, "argv", ["g", "--help"]):
        try:
            main()
        except SystemExit:
            pass
    output = capsys.readouterr().out
    assert "briefing" in output
    assert "calendar" in output
    assert "email" in output


def test_cli_unknown_command(capsys):
    import sys
    with patch.object(sys, "argv", ["g", "nonsense"]):
        try:
            main()
        except SystemExit:
            pass
    output = capsys.readouterr().out
    assert "Unknown command" in output


def test_full_calendar_flow(capsys):
    """Test g calendar today end-to-end."""
    import sys
    mock_events = {"items": [
        {"summary": "Team sync", "start": {"dateTime": "2026-03-05T10:00:00-05:00"}}
    ]}

    with patch.object(sys, "argv", ["g", "calendar", "today"]):
        with patch("mcgws.commands.calendar.gws_call", return_value=mock_events):
            with patch("mcgws.commands.calendar._get_config", return_value={"account": "test@example.com"}):
                main()

    output = capsys.readouterr().out
    assert "Team sync" in output


def test_full_email_flow(capsys):
    """Test g email end-to-end."""
    import sys
    mock_list = {"messages": [{"id": "abc"}]}
    mock_msg = {
        "id": "abc",
        "payload": {"headers": [
            {"name": "From", "value": "Client <client@example.com>"},
            {"name": "Subject", "value": "Proposal feedback"},
        ]},
        "labelIds": ["UNREAD"],
    }

    with patch.object(sys, "argv", ["g", "email"]):
        with patch("mcgws.commands.email.gws_call") as mock_gws:
            mock_gws.side_effect = [mock_list, mock_msg]
            with patch("mcgws.commands.email._get_config", return_value={"account": "test@example.com"}):
                main()

    output = capsys.readouterr().out
    assert "Client" in output
