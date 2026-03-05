"""Configuration loading and state management for mc-gws."""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "mc-gws"
CONFIG_FILE = CONFIG_DIR / "config.json"
FOLLOWUPS_FILE = CONFIG_DIR / "followups.json"
LOG_DIR = CONFIG_DIR / "logs"

REQUIRED_FIELDS = ["account", "self_reminder_phone"]
FOLLOWUP_PRUNE_DAYS = 14

DEFAULT_CONFIG = {
    "schedule": {
        "enabled": True,
        "timezone": "America/New_York",
        "briefing": "07:30",
        "midday": "12:00",
        "wrap": "17:00",
        "weekly_day": "monday",
        "skip_dates": [],
        "quiet_mode": False,
    },
    "briefing_sections": ["calendar", "email", "tasks", "drive", "notion", "followups"],
    "priority_keywords": ["invoice", "contract", "deadline", "urgent"],
    "followup_stale_days": 3,
    "notify_max_chars": 1500,
    "models": {"scheduled": "haiku", "interactive": "default"},
    "notion": {
        "meeting_notes_db": "",
        "projects_db": "",
        "clients_db": "",
        "people_db": "",
    },
    "vcfo": {"db_path": "", "enabled": False},
    "location": {"lat": None, "lon": None, "name": ""},
}


def ensure_dirs():
    """Create config and log directories if they don't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load configuration from JSON file. Applies defaults for missing keys."""
    ensure_dirs()
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Config not found at {CONFIG_FILE}. "
            f"Copy config.example.json to {CONFIG_FILE} and fill in your values."
        )
    with open(CONFIG_FILE) as f:
        config = json.load(f)

    for field in REQUIRED_FIELDS:
        if field not in config:
            raise ValueError(f"Missing required config field: {field}")

    # Apply defaults for missing optional keys
    for key, default in DEFAULT_CONFIG.items():
        if key not in config:
            config[key] = default
        elif isinstance(default, dict) and isinstance(config[key], dict):
            for subkey, subdefault in default.items():
                config[key].setdefault(subkey, subdefault)

    return config


def load_followups() -> dict:
    """Load follow-up tracking state. Prunes entries older than FOLLOWUP_PRUNE_DAYS.

    State format: {key: {"created_at": iso_ts, "description": str, "type": "outgoing"|"waiting", "due": iso_date|None}}
    """
    if not FOLLOWUPS_FILE.exists():
        return {}
    with open(FOLLOWUPS_FILE) as f:
        data = json.load(f)

    cutoff = datetime.now(timezone.utc) - timedelta(days=FOLLOWUP_PRUNE_DAYS)
    pruned = {}
    for key, value in data.items():
        ts = value.get("created_at")
        if ts is None:
            pruned[key] = value
        else:
            created = datetime.fromisoformat(ts)
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if created > cutoff:
                pruned[key] = value
    return pruned


def save_followups(followups: dict):
    """Save follow-up state to disk."""
    ensure_dirs()
    with open(FOLLOWUPS_FILE, "w") as f:
        json.dump(followups, f, indent=2)
