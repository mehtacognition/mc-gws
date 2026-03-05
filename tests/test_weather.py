"""Tests for weather module."""

from unittest.mock import patch, MagicMock
from mcgws.weather import fetch_weather, format_weather


def test_fetch_weather_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "current": {"temperature_2m": 72.4, "weather_code": 2},
        "daily": {
            "temperature_2m_max": [81.2],
            "temperature_2m_min": [58.7],
            "weather_code": [2],
        },
    }

    with patch("mcgws.weather._session_with_retries") as mock_session:
        mock_session.return_value.get.return_value = mock_response
        result = fetch_weather(33.749, -84.388)

    assert result["current_temp"] == 72
    assert result["current_desc"] == "partly cloudy"
    assert result["high"] == 81
    assert result["low"] == 59


def test_fetch_weather_failure():
    with patch("mcgws.weather._session_with_retries") as mock_session:
        mock_session.return_value.get.side_effect = Exception("Network error")
        result = fetch_weather(33.749, -84.388)

    assert result == {}


def test_format_weather_full():
    weather = {"current_temp": 72, "current_desc": "partly cloudy", "high": 81, "low": 59}
    result = format_weather(weather)
    assert "72°F" in result
    assert "partly cloudy" in result
    assert "high 81°F" in result
    assert "low 59°F" in result


def test_format_weather_empty():
    assert format_weather({}) == ""
    assert format_weather({"current_temp": None}) == ""
