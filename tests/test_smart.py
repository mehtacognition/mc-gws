import json
from unittest.mock import patch, MagicMock
from mcgws.commands.smart import run_briefing, run_chat


def test_run_briefing_interactive(capsys):
    mock_context = {
        "calendar": [{"summary": "Standup", "start": {"dateTime": "2026-03-05T09:00:00Z"}}],
        "email": [],
        "tasks": [],
        "drive": [],
        "followups": {},
    }

    with patch("mcgws.commands.smart._get_config", return_value={
        "account": "test@example.com",
        "models": {"scheduled": "haiku", "interactive": "default"},
        "briefing_sections": ["calendar", "email", "tasks", "drive", "followups"],
        "vcfo": {"enabled": False},
    }):
        with patch("mcgws.commands.smart._fetch_context", return_value=mock_context):
            with patch("mcgws.commands.smart.call_claude", return_value="The One Thing: Prepare for standup."):
                run_briefing([])

    output = capsys.readouterr().out
    assert "One Thing" in output


def test_run_briefing_notify():
    with patch("mcgws.commands.smart._get_config", return_value={
        "account": "test@example.com",
        "self_reminder_phone": "+15551234567",
        "models": {"scheduled": "haiku", "interactive": "default"},
        "briefing_sections": ["calendar"],
        "notify_max_chars": 1500,
        "vcfo": {"enabled": False},
    }):
        with patch("mcgws.commands.smart._fetch_context", return_value={"calendar": []}):
            with patch("mcgws.commands.smart.call_claude", return_value="Quiet morning."):
                with patch("mcgws.commands.smart.send_imessage") as mock_send:
                    run_briefing(["--notify"])

    mock_send.assert_called_once()
    assert "Quiet morning" in mock_send.call_args[0][1]


def test_run_briefing_error_notifies():
    with patch("mcgws.commands.smart._get_config", return_value={
        "account": "test@example.com",
        "self_reminder_phone": "+15551234567",
        "models": {"scheduled": "haiku", "interactive": "default"},
        "briefing_sections": ["calendar"],
        "vcfo": {"enabled": False},
    }):
        with patch("mcgws.commands.smart._fetch_context", side_effect=Exception("API down")):
            with patch("mcgws.commands.smart.notify_error") as mock_notify:
                run_briefing(["--notify"])

    mock_notify.assert_called_once()
    assert "failed" in mock_notify.call_args[0][1].lower()


def test_run_chat(capsys):
    with patch("mcgws.commands.smart._get_config", return_value={
        "account": "test@example.com",
        "models": {"interactive": "default"},
        "briefing_sections": ["calendar", "email", "tasks", "followups"],
    }):
        with patch("mcgws.commands.smart._fetch_context", return_value={"calendar": []}):
            with patch("mcgws.commands.smart.call_claude", return_value="Your calendar is clear today."):
                run_chat(["what's on my calendar"])

    output = capsys.readouterr().out
    assert "calendar is clear" in output
