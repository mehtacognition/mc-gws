import json
from mcgws.commands.followups import run


def test_list_followups_empty(capsys, tmp_config_dir):
    run([])
    output = capsys.readouterr().out
    assert "No active follow-ups" in output


def test_add_followup(capsys, tmp_config_dir):
    run(["add", "Waiting for Sarah's contract"])
    output = capsys.readouterr().out
    assert "Added" in output

    # Verify it was saved
    from mcgws.config import load_followups
    followups = load_followups()
    assert len(followups) == 1


def test_list_followups_with_items(capsys, tmp_config_dir):
    run(["add", "Waiting for contract"])
    run([])
    output = capsys.readouterr().out
    assert "contract" in output
