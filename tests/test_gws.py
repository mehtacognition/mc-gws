import json
import pytest
from unittest.mock import patch, MagicMock
from mcgws.gws import gws_call, GWSError


def test_gws_call_success():
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"files": []}'
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = gws_call("drive", "files", "list", params={"pageSize": 5}, account="test@example.com")

    assert result == {"files": []}
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert "drive" in call_args
    assert "files" in call_args


def test_gws_call_error():
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = '{"error": {"message": "Not found"}}'

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(GWSError, match="Not found"):
            gws_call("drive", "files", "list", account="test@example.com")


def test_gws_call_with_json_body():
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"id": "123"}'
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = gws_call("gmail", "users", "messages", "send",
                         json_body={"raw": "base64data"}, account="test@example.com")

    assert result == {"id": "123"}
    call_args = mock_run.call_args[0][0]
    assert "--json" in call_args
