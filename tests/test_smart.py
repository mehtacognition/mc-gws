import json
from unittest.mock import patch, MagicMock
from mcgws.commands.smart import run_briefing, run_chat, _parse_nudge, _handle_notify


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


def test_parse_nudge_extracts_nudge_line():
    text = "Full briefing content here.\n\nNUDGE: 81F | 4 meetings | Board prep is priority."
    body, nudge = _parse_nudge(text)
    assert "Full briefing content" in body
    assert "NUDGE:" not in body
    assert "81F" in nudge
    assert "Board prep" in nudge


def test_parse_nudge_strips_whitespace():
    text = "Body.\n\nNUDGE:   Weather is nice.  "
    body, nudge = _parse_nudge(text)
    assert nudge == "Weather is nice."
    assert body.strip() == "Body."


def test_parse_nudge_fallback_when_missing():
    text = "The One Thing: Focus on client meeting.\n\nMore details here."
    body, nudge = _parse_nudge(text)
    assert body == text
    assert "Focus on client meeting" in nudge


def test_parse_nudge_handles_nudge_with_newlines_before():
    text = "Content.\n\n\n\nNUDGE: Summary here."
    body, nudge = _parse_nudge(text)
    assert nudge == "Summary here."
    assert body.strip() == "Content."


def _make_notify_config(**overrides):
    base = {
        "account": "test@example.com",
        "self_reminder_phone": "+15551234567",
        "notify_max_chars": 1500,
        "notify_email": True,
        "notify_imessage": True,
        "email_subject_prefix": "[Chief of Staff]",
    }
    base.update(overrides)
    return base


def test_handle_notify_sends_email_and_imessage():
    config = _make_notify_config()
    output = "Full briefing.\n\nNUDGE: Priority is client meeting."

    with patch("mcgws.commands.smart.send_email_briefing") as mock_email:
        with patch("mcgws.commands.smart.send_imessage") as mock_imsg:
            _handle_notify(config, output, command_type="Morning Briefing")

    mock_email.assert_called_once()
    mock_imsg.assert_called_once()
    imsg_text = mock_imsg.call_args[0][1]
    assert "Priority is client meeting" in imsg_text
    assert "Full briefing in email" in imsg_text


def test_handle_notify_email_disabled():
    config = _make_notify_config(notify_email=False)
    output = "Content.\n\nNUDGE: Summary."

    with patch("mcgws.commands.smart.send_email_briefing") as mock_email:
        with patch("mcgws.commands.smart.send_imessage") as mock_imsg:
            _handle_notify(config, output, command_type="Morning Briefing")

    mock_email.assert_not_called()
    mock_imsg.assert_called_once()
    # When email disabled, iMessage gets full content (current behavior)
    assert "Content." in mock_imsg.call_args[0][1]


def test_handle_notify_imessage_disabled():
    config = _make_notify_config(notify_imessage=False)
    output = "Content.\n\nNUDGE: Summary."

    with patch("mcgws.commands.smart.send_email_briefing") as mock_email:
        with patch("mcgws.commands.smart.send_imessage") as mock_imsg:
            _handle_notify(config, output, command_type="Morning Briefing")

    mock_email.assert_called_once()
    mock_imsg.assert_not_called()


def test_handle_notify_email_failure_falls_back_to_full_imessage():
    config = _make_notify_config()
    output = "Full briefing.\n\nNUDGE: Summary."

    with patch("mcgws.commands.smart.send_email_briefing", side_effect=Exception("Gmail down")):
        with patch("mcgws.commands.smart.send_imessage") as mock_imsg:
            _handle_notify(config, output, command_type="Morning Briefing")

    mock_imsg.assert_called_once()
    # Should fall back to full content, not just nudge
    assert "Full briefing" in mock_imsg.call_args[0][1]


def test_handle_notify_subject_line_format():
    config = _make_notify_config()
    output = "Content.\n\nNUDGE: Summary."

    with patch("mcgws.commands.smart.send_email_briefing") as mock_email:
        with patch("mcgws.commands.smart.send_imessage"):
            _handle_notify(config, output, command_type="Morning Briefing")

    subject = mock_email.call_args[0][1]
    assert "[Chief of Staff]" in subject
    assert "Morning Briefing" in subject
