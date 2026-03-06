"""iMessage notification and error reporting."""

import base64
import logging
import subprocess
from email.mime.text import MIMEText

from mcgws.gws import gws_call

logger = logging.getLogger(__name__)


def send_imessage(phone_number: str, message: str):
    """Send an iMessage using AppleScript."""
    escaped_message = message.replace('"', '\\"')
    escaped_phone = phone_number.replace('"', '\\"')

    applescript = f'''
    tell application "Messages"
        set targetService to 1st account whose service type = iMessage
        set targetBuddy to participant "{escaped_phone}" of targetService
        send "{escaped_message}" to targetBuddy
    end tell
    '''

    result = subprocess.run(
        ["osascript", "-e", applescript],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to send iMessage: {result.stderr}")


def notify_error(config: dict, message: str):
    """Send an error notification to self via iMessage.

    No-op if self_reminder_phone is not configured.
    Fails silently if the notification itself fails.
    """
    phone = config.get("self_reminder_phone")
    if not phone:
        return
    try:
        send_imessage(phone, message)
    except Exception as e:
        logger.warning(f"Could not send error notification: {e}")


def send_email_briefing(config: dict, subject: str, html_body: str):
    """Send an HTML briefing email to self via Gmail API."""
    account = config["account"]

    msg = MIMEText(html_body, "html")
    msg["To"] = account
    msg["From"] = account
    msg["Subject"] = subject

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")

    gws_call(
        "gmail", "users", "messages", "send",
        json_body={"raw": raw},
        params={"userId": "me"},
        account=account,
    )
