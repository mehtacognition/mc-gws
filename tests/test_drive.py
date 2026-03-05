from unittest.mock import patch
from mcgws.commands.drive import run, run_docs, run_sheets


def test_run_search(capsys):
    mock_result = {"files": [
        {"name": "Q4 Report", "mimeType": "application/vnd.google-apps.spreadsheet", "modifiedTime": "2026-03-04T15:00:00Z"},
    ]}
    with patch("mcgws.commands.drive.gws_call", return_value=mock_result):
        with patch("mcgws.commands.drive._get_config", return_value={"account": "test@example.com"}):
            run(["quarterly report"])

    output = capsys.readouterr().out
    assert "Q4 Report" in output


def test_run_recent(capsys):
    mock_result = {"files": [
        {"name": "Notes", "mimeType": "application/vnd.google-apps.document", "modifiedTime": "2026-03-05T10:00:00Z"},
    ]}
    with patch("mcgws.commands.drive.gws_call", return_value=mock_result):
        with patch("mcgws.commands.drive._get_config", return_value={"account": "test@example.com"}):
            run(["recent"])

    output = capsys.readouterr().out
    assert "Notes" in output
