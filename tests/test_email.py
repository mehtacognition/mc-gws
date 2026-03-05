from unittest.mock import patch, call
from mcgws.commands.email import run, _fetch_messages, _read_message


def test_fetch_messages_unread():
    mock_list = {"messages": [{"id": "abc"}, {"id": "def"}]}
    mock_msg = {
        "id": "abc",
        "payload": {"headers": [
            {"name": "From", "value": "Sam <sam@example.com>"},
            {"name": "Subject", "value": "Budget Review"},
        ]},
        "labelIds": ["UNREAD"],
    }

    with patch("mcgws.commands.email.gws_call") as mock_gws:
        mock_gws.side_effect = [mock_list, mock_msg, mock_msg]
        msgs = _fetch_messages("test@example.com", query="is:unread", max_results=2)

    assert len(msgs) == 2


def test_run_unread(capsys):
    mock_list = {"messages": [{"id": "abc"}]}
    mock_msg = {
        "id": "abc",
        "payload": {"headers": [
            {"name": "From", "value": "Sam <sam@example.com>"},
            {"name": "Subject", "value": "Hello"},
        ]},
        "labelIds": ["UNREAD"],
    }

    with patch("mcgws.commands.email.gws_call") as mock_gws:
        mock_gws.side_effect = [mock_list, mock_msg]
        with patch("mcgws.commands.email._get_config", return_value={"account": "test@example.com"}):
            run([])

    output = capsys.readouterr().out
    assert "Sam" in output


def test_run_search(capsys):
    mock_list = {"messages": [{"id": "abc"}]}
    mock_msg = {
        "id": "abc",
        "payload": {"headers": [
            {"name": "From", "value": "John <john@example.com>"},
            {"name": "Subject", "value": "Invoice Q4"},
        ]},
        "labelIds": [],
    }

    with patch("mcgws.commands.email.gws_call") as mock_gws:
        mock_gws.side_effect = [mock_list, mock_msg]
        with patch("mcgws.commands.email._get_config", return_value={"account": "test@example.com"}):
            run(["from:john invoice"])

    output = capsys.readouterr().out
    assert "John" in output
