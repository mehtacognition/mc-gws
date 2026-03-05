from mcgws.formatting import format_calendar_event, format_email_summary, format_drive_file, truncate_for_notify


def test_format_calendar_event():
    event = {
        "summary": "Team standup",
        "start": {"dateTime": "2026-03-05T09:00:00-05:00"},
        "end": {"dateTime": "2026-03-05T09:30:00-05:00"},
    }
    result = format_calendar_event(event)
    assert "9:00 AM" in result
    assert "Team standup" in result


def test_format_calendar_event_all_day():
    event = {
        "summary": "Company Holiday",
        "start": {"date": "2026-03-05"},
        "end": {"date": "2026-03-06"},
    }
    result = format_calendar_event(event)
    assert "All day" in result
    assert "Company Holiday" in result


def test_format_email_summary():
    msg = {
        "id": "abc123",
        "payload": {
            "headers": [
                {"name": "From", "value": "Sam Chen <sam@example.com>"},
                {"name": "Subject", "value": "Re: Q4 Budget Review"},
                {"name": "Date", "value": "Wed, 5 Mar 2026 10:00:00 -0500"},
            ]
        },
        "labelIds": ["UNREAD", "INBOX"],
    }
    result = format_email_summary(msg)
    assert "Sam Chen" in result
    assert "Q4 Budget Review" in result


def test_format_drive_file():
    file = {
        "name": "Q4 Report",
        "mimeType": "application/vnd.google-apps.spreadsheet",
        "modifiedTime": "2026-03-04T15:00:00Z",
    }
    result = format_drive_file(file)
    assert "Q4 Report" in result
    assert "spreadsheet" in result.lower() or "Spreadsheet" in result


def test_truncate_for_notify():
    long_text = "A" * 2000
    result = truncate_for_notify(long_text, max_chars=1500)
    assert len(result) <= 1500
    assert result.endswith("...")


def test_truncate_for_notify_short_text():
    short_text = "Hello world"
    result = truncate_for_notify(short_text, max_chars=1500)
    assert result == "Hello world"
