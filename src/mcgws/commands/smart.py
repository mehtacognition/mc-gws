"""Smart path commands — LLM-powered via claude -p."""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

from mcgws.config import load_config, load_followups
from mcgws.gws import gws_call, GWSError
from mcgws.intelligence import call_claude
from mcgws.notify import send_imessage, notify_error, send_email_briefing
from mcgws.templates import wrap_briefing_html
from mcgws.formatting import truncate_for_notify
from mcgws.weather import fetch_weather, format_weather

logger = logging.getLogger(__name__)

NUDGE_INSTRUCTION = (
    '\n\nFinally, output a single line at the very end prefixed with "NUDGE:" containing '
    "a one-sentence iMessage summary with today's weather, meeting count, and the single "
    "most important agenda item. Example: "
    '"NUDGE: 81F, clear | 4 meetings | Board prep with Sarah at 2pm is your priority today."'
)


def _parse_nudge(text: str) -> tuple:
    """Parse NUDGE: line from Claude's response.

    Returns:
        (body, nudge) tuple. If no NUDGE: line found, nudge is first line truncated.
    """
    marker = "\nNUDGE:"
    idx = text.find(marker)
    if idx != -1:
        body = text[:idx].rstrip()
        nudge = text[idx + len(marker):].strip()
        nudge = nudge.split("\n")[0].strip()
        return body, nudge

    # Fallback: use first line
    first_line = text.split("\n")[0].strip()
    for prefix in ["**The One Thing:**", "The One Thing:"]:
        if first_line.startswith(prefix):
            first_line = first_line[len(prefix):].strip()
            break
    return text, first_line[:200]


def _get_config():
    return load_config()


def _model_for_mode(config: dict, args: list) -> str:
    """Determine which model to use based on --notify flag."""
    if "--notify" in args:
        return config.get("models", {}).get("scheduled", "haiku")
    return config.get("models", {}).get("interactive", "default")


def _fetch_context(account: str, sections: list) -> dict:
    """Pre-fetch data from all configured sections in parallel (sequential for now)."""
    context = {}

    if "calendar" in sections:
        try:
            from mcgws.commands.calendar import _fetch_events
            context["calendar"] = _fetch_events(account, "today")
        except GWSError as e:
            context["calendar_error"] = str(e)

    if "email" in sections:
        try:
            result = gws_call(
                "gmail", "users", "messages", "list",
                params={"userId": "me", "q": "is:unread", "maxResults": 10},
                account=account,
            )
            messages = []
            for msg_stub in result.get("messages", [])[:10]:
                msg = gws_call(
                    "gmail", "users", "messages", "get",
                    params={"userId": "me", "id": msg_stub["id"], "format": "metadata",
                            "metadataHeaders": ["From", "Subject", "Date"]},
                    account=account,
                )
                messages.append(msg)
            context["email"] = messages
        except GWSError as e:
            context["email_error"] = str(e)

    if "tasks" in sections:
        try:
            result = gws_call(
                "tasks", "tasks", "list",
                params={"tasklist": "@default", "showCompleted": False},
                account=account,
            )
            context["tasks"] = result.get("items", [])
        except GWSError as e:
            context["tasks_error"] = str(e)

    if "drive" in sections:
        try:
            result = gws_call(
                "drive", "files", "list",
                params={"pageSize": 10, "orderBy": "modifiedTime desc"},
                account=account,
            )
            context["drive"] = result.get("files", [])
        except GWSError as e:
            context["drive_error"] = str(e)

    if "followups" in sections:
        context["followups"] = load_followups()

    return context


def _fetch_weather_context(config: dict) -> str:
    """Fetch local weather if location is configured."""
    location = config.get("location", {})
    lat = location.get("lat")
    lon = location.get("lon")
    if lat is None or lon is None:
        return ""
    weather = fetch_weather(lat, lon)
    return format_weather(weather)


def _fetch_vcfo_snapshot(config: dict) -> str:
    """Fetch financial snapshot from vcfo if configured."""
    vcfo_config = config.get("vcfo", {})
    if not vcfo_config.get("enabled"):
        return ""
    db_path = vcfo_config.get("db_path", "")
    if not db_path:
        return ""
    try:
        import sys
        sys.path.insert(0, str(Path.home() / "Documents" / "cfo-project" / "src"))
        from vcfo.query import snapshot
        return snapshot(Path(db_path).expanduser())
    except Exception as e:
        logger.warning(f"vcfo snapshot failed: {e}")
        return ""


def _handle_notify(config: dict, output: str, command_type: str = "Briefing"):
    """Send briefing via email (full HTML) and iMessage (nudge).

    Fallback: if email fails, send full content via iMessage (original behavior).
    """
    from datetime import datetime as _dt

    phone = config.get("self_reminder_phone")
    send_email = config.get("notify_email", True)
    send_imsg = config.get("notify_imessage", True)
    prefix = config.get("email_subject_prefix", "[Chief of Staff]")

    body, nudge = _parse_nudge(output)
    date_str = _dt.now().strftime("%a %b %-d")
    subject = f"{prefix} {command_type} \u2014 {date_str}"

    email_sent = False

    # Step 1: Send email
    if send_email:
        try:
            html = wrap_briefing_html(body, command_type, date_str)
            send_email_briefing(config, subject, html)
            email_sent = True
        except Exception as e:
            logger.warning(f"Email send failed, falling back to iMessage: {e}")

    # Step 2: Send iMessage
    if send_imsg and phone:
        if email_sent:
            # Nudge only
            nudge_text = f"{nudge}\n\nFull briefing in email."
            send_imessage(phone, nudge_text)
        else:
            # Fallback: full content via iMessage (original behavior)
            max_chars = config.get("notify_max_chars", 1500)
            truncated = truncate_for_notify(output, max_chars)
            if len(output) > max_chars:
                truncated += "\n\nFull details: run `g briefing` in terminal."
            send_imessage(phone, truncated)


def run_briefing(args: list):
    """Morning strategic briefing."""
    start = time.time()
    config = _get_config()
    account = config["account"]
    model = _model_for_mode(config, args)

    try:
        sections = config.get("briefing_sections", ["calendar", "email", "tasks", "drive", "followups"])
        context = _fetch_context(account, sections)
        vcfo = _fetch_vcfo_snapshot(config)
        if vcfo:
            context["financial"] = vcfo

        weather = _fetch_weather_context(config)
        if weather:
            context["weather"] = weather

        prompt = (
            "Generate a strategic morning briefing. Lead with The One Thing — the single most important "
            "item that needs attention today. Include today's weather near the top. "
            "Then cover calendar, email highlights, pending tasks, "
            "and any stale follow-ups. Suggest specific actions with `g` CLI commands."
        )
        prompt += NUDGE_INSTRUCTION

        output = call_claude(prompt, json.dumps(context, default=str), model=model, config=config)

        if "--notify" in args:
            _handle_notify(config, output, command_type="Morning Briefing")
        else:
            print(output)

    except Exception as e:
        logger.error(f"Briefing failed: {e}")
        if "--notify" in args:
            now_local = datetime.now().strftime("%-I:%M %p")
            notify_error(config, f"Morning briefing failed at {now_local}: {e}")
        else:
            raise

    elapsed = time.time() - start
    logger.info(f"Briefing completed in {elapsed:.1f}s")


def run_midday(args: list):
    """Midday check-in."""
    config = _get_config()
    account = config["account"]
    model = _model_for_mode(config, args)

    try:
        context = _fetch_context(account, ["calendar", "email", "followups"])
        prompt = (
            "Generate a midday check-in. Focus on: anything urgent that arrived this morning, "
            "afternoon meeting prep needed, and any follow-ups becoming stale. Be brief."
        )
        prompt += NUDGE_INSTRUCTION
        output = call_claude(prompt, json.dumps(context, default=str), model=model, config=config)

        if "--notify" in args:
            _handle_notify(config, output, command_type="Midday Check-in")
        else:
            print(output)
    except Exception as e:
        logger.error(f"Midday check-in failed: {e}")
        if "--notify" in args:
            notify_error(config, f"Midday check-in failed: {e}")
        else:
            raise


def run_prep(args: list):
    """Meeting preparation."""
    config = _get_config()
    account = config["account"]
    model = _model_for_mode(config, args)

    if not args or args[0] == "--notify":
        print("Usage: g prep \"meeting name or keyword\"")
        return

    meeting_query = " ".join(a for a in args if a != "--notify")

    try:
        # Fetch calendar events to find the meeting
        from mcgws.commands.calendar import _fetch_events
        events = _fetch_events(account, "today") + _fetch_events(account, "tomorrow")

        # Search emails related to the meeting topic
        email_result = gws_call(
            "gmail", "users", "messages", "list",
            params={"userId": "me", "q": meeting_query, "maxResults": 5},
            account=account,
        )
        emails = []
        for msg_stub in email_result.get("messages", [])[:5]:
            msg = gws_call(
                "gmail", "users", "messages", "get",
                params={"userId": "me", "id": msg_stub["id"], "format": "metadata",
                        "metadataHeaders": ["From", "Subject", "Date"]},
                account=account,
            )
            emails.append(msg)

        # Search drive for related docs
        drive_result = gws_call(
            "drive", "files", "list",
            params={"q": f"name contains '{meeting_query}'", "pageSize": 5},
            account=account,
        )

        context = {
            "meeting_query": meeting_query,
            "calendar_events": events,
            "related_emails": emails,
            "related_drive_files": drive_result.get("files", []),
            "followups": load_followups(),
        }

        prompt = (
            f"Prepare me for a meeting about: {meeting_query}. "
            "Find the relevant calendar event, summarize related emails and documents, "
            "surface any commitments I made in previous interactions, "
            "and suggest what I should prepare or bring up. "
            "Include attendee context if available."
        )

        output = call_claude(prompt, json.dumps(context, default=str), model=model, config=config)
        print(output)

    except Exception as e:
        logger.error(f"Meeting prep failed: {e}")
        raise


def run_wrap(args: list):
    """End-of-day summary."""
    config = _get_config()
    account = config["account"]
    model = _model_for_mode(config, args)

    try:
        context = _fetch_context(account, ["calendar", "email", "tasks", "followups"])

        # Also fetch tomorrow's calendar
        from mcgws.commands.calendar import _fetch_events
        context["tomorrow_calendar"] = _fetch_events(account, "tomorrow")

        prompt = (
            "Generate an end-of-day wrap-up. Cover: what happened today (based on calendar), "
            "what's still open (unread emails, pending tasks, stale follow-ups), "
            "and what's coming tomorrow. Flag anything that needs attention before tomorrow. "
            "End with a suggested first action for tomorrow morning."
        )
        prompt += NUDGE_INSTRUCTION

        output = call_claude(prompt, json.dumps(context, default=str), model=model, config=config)

        if "--notify" in args:
            _handle_notify(config, output, command_type="End-of-Day Wrap")
        else:
            print(output)
    except Exception as e:
        logger.error(f"Wrap-up failed: {e}")
        if "--notify" in args:
            notify_error(config, f"End-of-day wrap failed: {e}")
        else:
            raise


def run_weekly(args: list):
    """Monday weekly overview."""
    config = _get_config()
    account = config["account"]
    model = _model_for_mode(config, args)

    try:
        # Fetch this week's calendar
        from mcgws.commands.calendar import _fetch_events
        week_events = _fetch_events(account, "week")

        # Fetch last week's sent emails (for open threads)
        from datetime import timedelta, timezone
        one_week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y/%m/%d")
        email_result = gws_call(
            "gmail", "users", "messages", "list",
            params={"userId": "me", "q": f"is:sent after:{one_week_ago}", "maxResults": 20},
            account=account,
        )

        context = {
            "week_calendar": week_events,
            "sent_last_week": email_result.get("messages", []),
            "followups": load_followups(),
            "tasks": [],
        }

        # Google Tasks
        try:
            tasks_result = gws_call(
                "tasks", "tasks", "list",
                params={"tasklist": "@default", "showCompleted": False},
                account=account,
            )
            context["tasks"] = tasks_result.get("items", [])
        except GWSError:
            pass

        # vcfo financial snapshot
        vcfo = _fetch_vcfo_snapshot(config)
        if vcfo:
            context["financial"] = vcfo

        prompt = (
            "Generate a Monday weekly overview. Cover: "
            "1. The One Thing this week — single most important focus area. "
            "2. Week ahead calendar with conflict warnings. "
            "3. Open threads from last week (emails sent but not replied to). "
            "4. Pending tasks and follow-ups. "
            "5. Financial snapshot if available. "
            "6. Any patterns you notice (meeting load, over-indexing on one client, etc.)."
        )
        prompt += NUDGE_INSTRUCTION

        output = call_claude(prompt, json.dumps(context, default=str), model=model, config=config)

        if "--notify" in args:
            _handle_notify(config, output, command_type="Weekly Digest")
        else:
            print(output)
    except Exception as e:
        logger.error(f"Weekly digest failed: {e}")
        if "--notify" in args:
            notify_error(config, f"Weekly digest failed: {e}")
        else:
            raise


def run_chat(args: list):
    """Freeform conversational chief of staff."""
    if not args:
        print("Usage: g chat \"your question or request\"")
        return

    config = _get_config()
    account = config["account"]
    model = config.get("models", {}).get("interactive", "default")
    query = " ".join(args)

    try:
        # Fetch broad context for the conversation
        context = _fetch_context(account, ["calendar", "email", "tasks", "followups"])

        prompt = (
            f"The user asks: {query}\n\n"
            "Answer using the data provided. If you need to suggest actions, "
            "provide exact `g` CLI commands. Be helpful and concise."
        )

        output = call_claude(prompt, json.dumps(context, default=str), model=model, config=config)
        print(output)

    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise
