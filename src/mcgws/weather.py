"""Fetch local weather from Open-Meteo API (free, no API key needed)."""

import logging
from datetime import datetime, timezone

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# WMO Weather interpretation codes (WMO 4677)
WMO_DESCRIPTIONS = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "depositing rime fog",
    51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
    56: "light freezing drizzle", 57: "dense freezing drizzle",
    61: "slight rain", 63: "moderate rain", 65: "heavy rain",
    66: "light freezing rain", 67: "heavy freezing rain",
    71: "slight snow", 73: "moderate snow", 75: "heavy snow", 77: "snow grains",
    80: "slight rain showers", 81: "moderate rain showers", 82: "violent rain showers",
    85: "slight snow showers", 86: "heavy snow showers",
    95: "thunderstorm", 96: "thunderstorm with slight hail", 99: "thunderstorm with heavy hail",
}


def _session_with_retries():
    """Create a requests Session with automatic retry."""
    session = requests.Session()
    retry = Retry(total=2, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504))
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session


def fetch_weather(lat: float, lon: float) -> dict:
    """Fetch current weather and today's forecast for a location.

    Returns dict with keys: current_temp, current_desc, high, low, or empty dict on failure.
    """
    try:
        session = _session_with_retries()
        params = {
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "current": "temperature_2m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,weather_code",
            "temperature_unit": "fahrenheit",
            "timezone": "auto",
            "forecast_days": 1,
        }
        response = session.get(OPEN_METEO_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        current = data.get("current", {})
        daily = data.get("daily", {})

        current_temp = current.get("temperature_2m")
        current_code = current.get("weather_code", 0)
        highs = daily.get("temperature_2m_max", [])
        lows = daily.get("temperature_2m_min", [])

        return {
            "current_temp": round(current_temp) if current_temp is not None else None,
            "current_desc": WMO_DESCRIPTIONS.get(current_code, "unknown"),
            "high": round(highs[0]) if highs else None,
            "low": round(lows[0]) if lows else None,
        }
    except Exception:
        logger.warning("Failed to fetch weather", exc_info=True)
        return {}


def format_weather(weather: dict) -> str:
    """Format weather dict into a one-line summary."""
    if not weather or weather.get("current_temp") is None:
        return ""

    temp = weather["current_temp"]
    desc = weather.get("current_desc", "")
    high = weather.get("high")
    low = weather.get("low")

    parts = [f"{temp}°F, {desc}"]
    if high is not None and low is not None:
        parts.append(f"high {high}°F, low {low}°F")

    return " — ".join(parts)
