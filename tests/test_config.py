import json
import pytest
from mcgws.config import load_config, load_followups, save_followups


def test_load_config_missing_file(tmp_config_dir):
    with pytest.raises(FileNotFoundError, match="Config not found"):
        load_config()


def test_load_config_missing_required_field(tmp_config_dir):
    config_path = tmp_config_dir / "config.json"
    config_path.write_text(json.dumps({"account": "test@example.com"}))
    with pytest.raises(ValueError, match="self_reminder_phone"):
        load_config()


def test_load_config_applies_defaults(config_file):
    config = load_config()
    assert config["account"] == "test@example.com"
    assert config["schedule"]["briefing"] == "07:30"
    assert config["models"]["scheduled"] == "haiku"
    assert config["followup_stale_days"] == 3


def test_load_config_preserves_user_values(tmp_config_dir):
    config_path = tmp_config_dir / "config.json"
    config_path.write_text(json.dumps({
        "account": "test@example.com",
        "self_reminder_phone": "+15551234567",
        "followup_stale_days": 7,
    }))
    config = load_config()
    assert config["followup_stale_days"] == 7


def test_load_followups_empty(tmp_config_dir):
    result = load_followups()
    assert result == {}


def test_save_and_load_followups(tmp_config_dir):
    followups = {
        "key1": {
            "created_at": "2026-03-05T12:00:00+00:00",
            "description": "Waiting for contract",
            "type": "waiting",
            "due": None,
        }
    }
    save_followups(followups)
    loaded = load_followups()
    assert "key1" in loaded
    assert loaded["key1"]["description"] == "Waiting for contract"


def test_followups_prunes_old_entries(tmp_config_dir):
    followups = {
        "old": {
            "created_at": "2020-01-01T00:00:00+00:00",
            "description": "Ancient item",
            "type": "outgoing",
            "due": None,
        },
        "new": {
            "created_at": "2026-03-05T00:00:00+00:00",
            "description": "Recent item",
            "type": "waiting",
            "due": None,
        },
    }
    save_followups(followups)
    loaded = load_followups()
    assert "old" not in loaded
    assert "new" in loaded
