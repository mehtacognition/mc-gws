from unittest.mock import patch
from mcgws.commands.tasks import run


def test_list_tasks(capsys):
    mock_result = {
        "items": [
            {"title": "Follow up with client", "status": "needsAction"},
            {"title": "Review proposal", "status": "needsAction"},
        ]
    }
    with patch("mcgws.commands.tasks.gws_call", return_value=mock_result):
        with patch("mcgws.commands.tasks._get_config", return_value={"account": "test@example.com"}):
            run([])

    output = capsys.readouterr().out
    assert "Follow up" in output


def test_add_task(capsys):
    mock_result = {"title": "New task"}
    with patch("mcgws.commands.tasks.gws_call", return_value=mock_result):
        with patch("mcgws.commands.tasks._get_config", return_value={"account": "test@example.com"}):
            run(["add", "New task"])

    output = capsys.readouterr().out
    assert "Added" in output or "New task" in output
