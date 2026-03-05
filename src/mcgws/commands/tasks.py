"""Google Tasks command — fast path, no LLM."""

from mcgws.config import load_config
from mcgws.gws import gws_call


def _get_config():
    return load_config()


def run(args: list):
    """Execute tasks subcommand."""
    config = _get_config()
    account = config["account"]

    if not args:
        # List tasks from default task list
        result = gws_call(
            "tasks", "tasks", "list",
            params={"tasklist": "@default", "showCompleted": False},
            account=account,
        )
        items = result.get("items", [])
        if not items:
            print("No pending tasks.")
            return

        print(f"\n✅ Google Tasks ({len(items)} pending)\n")
        for task in items:
            title = task.get("title", "(Untitled)")
            due = task.get("due", "")
            due_str = f" (due {due[:10]})" if due else ""
            print(f"  □ {title}{due_str}")
        print()

    elif args[0] == "add" and len(args) >= 2:
        title = " ".join(args[1:])
        result = gws_call(
            "tasks", "tasks", "insert",
            params={"tasklist": "@default"},
            json_body={"title": title},
            account=account,
        )
        print(f"Added: {title}")

    else:
        print("Usage: g tasks | g tasks add \"title\"")
