"""Follow-up tracking command — fast path, local state."""

import hashlib
from datetime import datetime, timezone
from mcgws.config import load_followups, save_followups


def run(args: list):
    """Execute followups subcommand."""
    if not args:
        _list_followups()
    elif args[0] == "add" and len(args) >= 2:
        desc = " ".join(args[1:])
        due = None
        # Parse --due flag
        if "--due" in args:
            due_idx = args.index("--due")
            if due_idx + 1 < len(args):
                due = args[due_idx + 1]
                desc = " ".join(args[1:due_idx])
        _add_followup(desc, due=due)
    elif args[0] == "done" and len(args) >= 2:
        _complete_followup(args[1])
    else:
        print("Usage: g followups | g followups add \"desc\" [--due DATE] | g followups done <key>")


def _list_followups():
    followups = load_followups()
    if not followups:
        print("No active follow-ups.")
        return

    outgoing = {k: v for k, v in followups.items() if v.get("type") == "outgoing"}
    waiting = {k: v for k, v in followups.items() if v.get("type") == "waiting"}

    if outgoing:
        print(f"\n📤 Outgoing commitments ({len(outgoing)})\n")
        for key, item in sorted(outgoing.items(), key=lambda x: x[1].get("created_at", "")):
            _print_followup(key, item)

    if waiting:
        print(f"\n📥 Waiting for ({len(waiting)})\n")
        for key, item in sorted(waiting.items(), key=lambda x: x[1].get("created_at", "")):
            _print_followup(key, item)

    if not outgoing and not waiting:
        print("No active follow-ups.")

    print()


def _print_followup(key: str, item: dict):
    desc = item.get("description", "")
    created = item.get("created_at", "")
    due = item.get("due")
    age = ""
    if created:
        created_dt = datetime.fromisoformat(created)
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone.utc)
        days = (datetime.now(timezone.utc) - created_dt).days
        age = f" ({days}d ago)"
    due_str = f" [due {due}]" if due else ""
    print(f"  □ {desc}{due_str}{age}")
    print(f"    key: {key[:8]}")


def _add_followup(description: str, followup_type: str = "waiting", due: str = None):
    followups = load_followups()
    key = hashlib.sha256(f"{description}{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:16]
    followups[key] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": description,
        "type": followup_type,
        "due": due,
    }
    save_followups(followups)
    print(f"Added follow-up: {description}")


def _complete_followup(key_prefix: str):
    followups = load_followups()
    matches = [k for k in followups if k.startswith(key_prefix)]
    if not matches:
        print(f"No follow-up found matching: {key_prefix}")
        return
    if len(matches) > 1:
        print(f"Ambiguous key prefix — matches {len(matches)} items. Be more specific.")
        return
    desc = followups[matches[0]].get("description", "")
    del followups[matches[0]]
    save_followups(followups)
    print(f"Completed: {desc}")
