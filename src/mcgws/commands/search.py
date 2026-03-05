"""Unified search across Drive, Gmail, Calendar — fast path, no LLM."""

from mcgws.config import load_config
from mcgws.gws import gws_call
from mcgws.formatting import format_drive_file, format_email_summary, format_calendar_event


def _get_config():
    return load_config()


def run(args: list):
    """Search across Drive, Gmail, and Calendar."""
    if not args:
        print("Usage: g search \"query\"")
        return

    config = _get_config()
    account = config["account"]
    query = " ".join(args)

    print(f"\n🔍 Search: \"{query}\"\n")

    # Drive
    try:
        drive_result = gws_call(
            "drive", "files", "list",
            params={"q": f"name contains '{query}' or fullText contains '{query}'", "pageSize": 5},
            account=account,
        )
        files = drive_result.get("files", [])
        if files:
            print(f"📁 Drive ({len(files)} results)")
            for f in files:
                print(format_drive_file(f))
            print()
    except Exception:
        pass

    # Gmail
    try:
        email_result = gws_call(
            "gmail", "users", "messages", "list",
            params={"userId": "me", "q": query, "maxResults": 5},
            account=account,
        )
        messages = email_result.get("messages", [])
        if messages:
            print(f"📧 Email ({len(messages)} results)")
            for msg_stub in messages:
                msg = gws_call(
                    "gmail", "users", "messages", "get",
                    params={"userId": "me", "id": msg_stub["id"], "format": "metadata",
                            "metadataHeaders": ["From", "Subject"]},
                    account=account,
                )
                print(format_email_summary(msg))
            print()
    except Exception:
        pass

    # Calendar (search upcoming 30 days)
    try:
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        cal_result = gws_call(
            "calendar", "events", "list",
            params={
                "calendarId": "primary",
                "q": query,
                "timeMin": now.isoformat(),
                "timeMax": (now + timedelta(days=30)).isoformat(),
                "singleEvents": True,
                "orderBy": "startTime",
                "maxResults": 5,
            },
            account=account,
        )
        events = cal_result.get("items", [])
        if events:
            print(f"📅 Calendar ({len(events)} results)")
            for event in events:
                print(format_calendar_event(event))
            print()
    except Exception:
        pass
