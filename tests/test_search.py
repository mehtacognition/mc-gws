from unittest.mock import patch
from mcgws.commands.search import run


def test_unified_search(capsys):
    mock_drive = {"files": [{"name": "Budget.xlsx", "mimeType": "application/vnd.google-apps.spreadsheet", "modifiedTime": "2026-03-04T00:00:00Z"}]}
    mock_email = {"messages": [{"id": "abc"}]}
    mock_msg = {"id": "abc", "payload": {"headers": [
        {"name": "From", "value": "Sam <sam@example.com>"},
        {"name": "Subject", "value": "Budget discussion"},
    ]}, "labelIds": []}
    mock_cal = {"items": [{"summary": "Budget Review", "start": {"dateTime": "2026-03-05T14:00:00Z"}}]}

    with patch("mcgws.commands.search.gws_call") as mock_gws:
        mock_gws.side_effect = [mock_drive, mock_email, mock_msg, mock_cal]
        with patch("mcgws.commands.search._get_config", return_value={"account": "test@example.com"}):
            run(["budget"])

    output = capsys.readouterr().out
    assert "Budget" in output
