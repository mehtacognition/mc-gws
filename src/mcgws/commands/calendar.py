"""Calendar command — fast path, no LLM."""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from mcgws.config import load_config
from mcgws.gws import gws_call
from mcgws.formatting import format_calendar_event


def _get_config():
    return load_config()


def _date_range(period: str, tz_name: str = "America/New_York") -> tuple:
    """Return ISO start/end for a period in the user's local timezone."""
    local_tz = ZoneInfo(tz_name)
    now = datetime.now(local_tz)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "tomorrow":
        start = today_start + timedelta(days=1)
        end = start + timedelta(days=1)
    elif period == "week":
        start = today_start
        end = start + timedelta(days=7)
    else:  # today (default)
        start = today_start
        end = start + timedelta(days=1)

    return start.isoformat(), end.isoformat()


def _fetch_events(account: str, period: str = "today", tz_name: str = "America/New_York") -> list:
    """Fetch calendar events for a period."""
    time_min, time_max = _date_range(period, tz_name)
    result = gws_call(
        "calendar", "events", "list",
        params={
            "calendarId": "primary",
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": True,
            "orderBy": "startTime",
        },
        account=account,
    )
    return result.get("items", [])


def _find_conflicts(events: list) -> list:
    """Find overlapping events."""
    conflicts = []
    sorted_events = sorted(events, key=lambda e: e.get("start", {}).get("dateTime", ""))
    for i in range(len(sorted_events) - 1):
        end_i = sorted_events[i].get("end", {}).get("dateTime")
        start_next = sorted_events[i + 1].get("start", {}).get("dateTime")
        if end_i and start_next and end_i > start_next:
            conflicts.append((sorted_events[i], sorted_events[i + 1]))
    return conflicts


def run(args: list):
    """Execute calendar subcommand."""
    config = _get_config()
    account = config["account"]
    tz_name = config.get("schedule", {}).get("timezone", "America/New_York")

    if not args or args[0] in ("today", "tomorrow", "week"):
        period = args[0] if args else "today"
        events = _fetch_events(account, period, tz_name)

        if not events:
            print(f"No events {period}.")
            return

        print(f"\n📅 Calendar — {period.title()} ({len(events)} events)\n")
        for event in events:
            print(format_calendar_event(event))
        print()

    elif args[0] == "conflicts":
        events = _fetch_events(account, "week", tz_name)
        conflicts = _find_conflicts(events)
        if not conflicts:
            print("No calendar conflicts this week.")
            return
        print(f"\n⚠️  {len(conflicts)} conflict(s) found:\n")
        for e1, e2 in conflicts:
            print(f"  {e1.get('summary', '?')} overlaps with {e2.get('summary', '?')}")
        print()

    elif args[0] == "add" and len(args) >= 4:
        title = args[1]
        day = args[2]
        time_str = args[3]
        # Minimal event creation — could be enhanced
        result = gws_call(
            "calendar", "events", "insert",
            params={"calendarId": "primary"},
            json_body={
                "summary": title,
                "start": {"dateTime": f"{day}T{time_str}:00"},
                "end": {"dateTime": f"{day}T{time_str}:00"},  # 1hr default added by API
            },
            account=account,
        )
        print(f"Created: {result.get('summary', title)}")

    else:
        print("Usage: g calendar [today|tomorrow|week|conflicts]")
        print("       g calendar add \"title\" YYYY-MM-DD HH:MM")
