import json
from unittest.mock import patch
from mcgws.commands.calendar import run, _fetch_events


def test_fetch_events_today():
    mock_events = {
        "items": [
            {"summary": "Standup", "start": {"dateTime": "2026-03-05T09:00:00-05:00"}},
            {"summary": "Lunch", "start": {"dateTime": "2026-03-05T12:00:00-05:00"}},
        ]
    }

    with patch("mcgws.commands.calendar.gws_call", return_value=mock_events):
        events = _fetch_events("test@example.com", "today")

    assert len(events) == 2
    assert events[0]["summary"] == "Standup"


def test_run_today(capsys):
    mock_events = {
        "items": [
            {"summary": "Standup", "start": {"dateTime": "2026-03-05T09:00:00-05:00"}},
        ]
    }

    with patch("mcgws.commands.calendar.gws_call", return_value=mock_events):
        with patch("mcgws.commands.calendar._get_config", return_value={"account": "test@example.com"}):
            run(["today"])

    output = capsys.readouterr().out
    assert "Standup" in output


def test_run_no_events(capsys):
    with patch("mcgws.commands.calendar.gws_call", return_value={"items": []}):
        with patch("mcgws.commands.calendar._get_config", return_value={"account": "test@example.com"}):
            run(["today"])

    output = capsys.readouterr().out
    assert "No events" in output
