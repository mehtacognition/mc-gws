"""Output formatting utilities for terminal and iMessage."""

from datetime import datetime


def _parse_datetime(dt_str: str) -> datetime:
    """Parse a datetime string from Google APIs."""
    # Handle both offset and Z formats
    dt_str = dt_str.replace("Z", "+00:00")
    return datetime.fromisoformat(dt_str)


def _extract_header(msg: dict, name: str) -> str:
    """Extract a header value from a Gmail message."""
    headers = msg.get("payload", {}).get("headers", [])
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def _friendly_name(from_header: str) -> str:
    """Extract display name from 'Name <email>' format."""
    if "<" in from_header:
        return from_header.split("<")[0].strip().strip('"')
    return from_header


def _mime_label(mime_type: str) -> str:
    """Convert Google MIME type to a friendly label."""
    labels = {
        "application/vnd.google-apps.document": "Doc",
        "application/vnd.google-apps.spreadsheet": "Spreadsheet",
        "application/vnd.google-apps.presentation": "Slides",
        "application/vnd.google-apps.form": "Form",
        "application/vnd.google-apps.folder": "Folder",
        "application/pdf": "PDF",
    }
    return labels.get(mime_type, "File")


def format_calendar_event(event: dict) -> str:
    """Format a calendar event for terminal display."""
    summary = event.get("summary", "(No title)")
    start = event.get("start", {})

    if "dateTime" in start:
        dt = _parse_datetime(start["dateTime"])
        time_str = dt.strftime("%-I:%M %p")
    elif "date" in start:
        time_str = "All day"
    else:
        time_str = "?"

    location = event.get("location", "")
    hangout = event.get("hangoutLink", "")
    extra = ""
    if hangout:
        extra = " (Google Meet)"
    elif location:
        extra = f" ({location})"

    return f"  {time_str:>10}  {summary}{extra}"


def format_email_summary(msg: dict) -> str:
    """Format a Gmail message as a one-line summary."""
    from_val = _extract_header(msg, "From")
    subject = _extract_header(msg, "Subject") or "(No subject)"
    sender = _friendly_name(from_val)
    labels = msg.get("labelIds", [])
    star = "★" if "UNREAD" in labels else " "
    return f"  {star} {sender} — {subject}"


def format_drive_file(file: dict) -> str:
    """Format a Drive file for terminal display."""
    name = file.get("name", "(Untitled)")
    mime = file.get("mimeType", "")
    label = _mime_label(mime)
    modified = file.get("modifiedTime", "")
    mod_str = ""
    if modified:
        dt = _parse_datetime(modified)
        mod_str = f", modified {dt.strftime('%b %-d')}"
    return f"  {name} ({label}{mod_str})"


def truncate_for_notify(text: str, max_chars: int = 1500) -> str:
    """Truncate text for iMessage notification."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."
