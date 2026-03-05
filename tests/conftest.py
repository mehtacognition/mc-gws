import json
import pytest
from pathlib import Path


@pytest.fixture
def tmp_config_dir(tmp_path, monkeypatch):
    """Set up a temporary config directory for testing."""
    config_dir = tmp_path / "config" / "mc-gws"
    config_dir.mkdir(parents=True)
    (config_dir / "logs").mkdir()
    monkeypatch.setattr("mcgws.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("mcgws.config.CONFIG_FILE", config_dir / "config.json")
    monkeypatch.setattr("mcgws.config.FOLLOWUPS_FILE", config_dir / "followups.json")
    monkeypatch.setattr("mcgws.config.LOG_DIR", config_dir / "logs")
    return config_dir


@pytest.fixture
def sample_config():
    """Return a minimal valid config dict."""
    return {
        "account": "test@example.com",
        "self_reminder_phone": "+15551234567",
    }


@pytest.fixture
def config_file(tmp_config_dir, sample_config):
    """Write a sample config file and return its path."""
    config_path = tmp_config_dir / "config.json"
    config_path.write_text(json.dumps(sample_config))
    return config_path
