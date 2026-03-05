"""Email command — fast path, no LLM. Full email actions: read, reply, send, forward, draft, label, archive."""

import base64
import json
from email.mime.text import MIMEText
from mcgws.config import load_config
from mcgws.gws import gws_call
from mcgws.formatting import format_email_summary, _extract_header


def _get_config():
    return load_config()


def _fetch_messages(account: str, query: str = "is:unread", max_results: int = 10) -> list:
    """Fetch message list and hydrate with full message data."""
    result = gws_call(
        "gmail", "users", "messages", "list",
        params={"userId": "me", "q": query, "maxResults": max_results},
        account=account,
    )
    messages = result.get("messages", [])

    hydrated = []
    for msg_stub in messages:
        msg = gws_call(
            "gmail", "users", "messages", "get",
            params={"userId": "me", "id": msg_stub["id"], "format": "full"},
            account=account,
        )
        hydrated.append(msg)
    return hydrated


def _read_message(account: str, msg_id: str) -> dict:
    """Fetch a single full message."""
    return gws_call(
        "gmail", "users", "messages", "get",
        params={"userId": "me", "id": msg_id, "format": "full"},
        account=account,
    )


def _decode_body(msg: dict) -> str:
    """Extract plain text body from a Gmail message."""
    payload = msg.get("payload", {})

    # Simple message
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    # Multipart — find text/plain part
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    return "(No plain text body)"


def _create_raw_message(to: str, subject: str, body: str, reply_to_msg: dict = None) -> str:
    """Create a base64url-encoded RFC 2822 message."""
    msg = MIMEText(body)
    msg["To"] = to
    msg["Subject"] = subject

    if reply_to_msg:
        msg_id = _extract_header(reply_to_msg, "Message-Id")
        if msg_id:
            msg["In-Reply-To"] = msg_id
            msg["References"] = msg_id
        thread_subject = _extract_header(reply_to_msg, "Subject")
        if thread_subject and not thread_subject.startswith("Re:"):
            msg["Subject"] = f"Re: {thread_subject}"

    return base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")


def run(args: list):
    """Execute email subcommand."""
    config = _get_config()
    account = config["account"]

    if not args:
        # Default: show unread
        messages = _fetch_messages(account, "is:unread", max_results=10)
        if not messages:
            print("No unread emails.")
            return
        print(f"\n📧 Email — {len(messages)} unread\n")
        for msg in messages:
            print(format_email_summary(msg))
            print(f"         ID: {msg['id']}")
        print()

    elif args[0] == "read" and len(args) >= 2:
        msg = _read_message(account, args[1])
        subject = _extract_header(msg, "Subject")
        sender = _extract_header(msg, "From")
        date = _extract_header(msg, "Date")
        body = _decode_body(msg)
        print(f"\nFrom: {sender}")
        print(f"Subject: {subject}")
        print(f"Date: {date}")
        print(f"\n{body}")

    elif args[0] == "reply" and len(args) >= 3:
        msg_id = args[1]
        body = " ".join(args[2:])
        original = _read_message(account, msg_id)
        sender = _extract_header(original, "From")
        # Extract email from "Name <email>" format
        reply_to = sender.split("<")[-1].rstrip(">") if "<" in sender else sender
        raw = _create_raw_message(reply_to, "", body, reply_to_msg=original)
        thread_id = original.get("threadId")
        result = gws_call(
            "gmail", "users", "messages", "send",
            json_body={"raw": raw, "threadId": thread_id},
            params={"userId": "me"},
            account=account,
        )
        print(f"Replied to {sender}.")

    elif args[0] == "send" and len(args) >= 4:
        to = args[1]
        subject = args[2]
        body = " ".join(args[3:])
        raw = _create_raw_message(to, subject, body)
        gws_call(
            "gmail", "users", "messages", "send",
            json_body={"raw": raw},
            params={"userId": "me"},
            account=account,
        )
        print(f"Sent to {to}.")

    elif args[0] == "forward" and len(args) >= 3:
        msg_id = args[1]
        to = args[2]
        original = _read_message(account, msg_id)
        subject = _extract_header(original, "Subject")
        body = _decode_body(original)
        fwd_body = f"---------- Forwarded message ----------\n{body}"
        raw = _create_raw_message(to, f"Fwd: {subject}", fwd_body)
        gws_call(
            "gmail", "users", "messages", "send",
            json_body={"raw": raw},
            params={"userId": "me"},
            account=account,
        )
        print(f"Forwarded to {to}.")

    elif args[0] == "draft" and len(args) >= 4:
        to = args[1]
        subject = args[2]
        body = " ".join(args[3:])
        raw = _create_raw_message(to, subject, body)
        gws_call(
            "gmail", "users", "drafts", "create",
            json_body={"message": {"raw": raw}},
            params={"userId": "me"},
            account=account,
        )
        print(f"Draft created for {to}.")

    elif args[0] == "label" and len(args) >= 3:
        msg_id = args[1]
        label = args[2]
        gws_call(
            "gmail", "users", "messages", "modify",
            params={"userId": "me", "id": msg_id},
            json_body={"addLabelIds": [label.upper()]},
            account=account,
        )
        print(f"Labeled {msg_id} as {label}.")

    elif args[0] == "archive" and len(args) >= 2:
        msg_id = args[1]
        gws_call(
            "gmail", "users", "messages", "modify",
            params={"userId": "me", "id": msg_id},
            json_body={"removeLabelIds": ["INBOX"]},
            account=account,
        )
        print(f"Archived {msg_id}.")

    else:
        # Search query
        query = " ".join(args)
        messages = _fetch_messages(account, query, max_results=10)
        if not messages:
            print(f"No emails matching: {query}")
            return
        print(f"\n📧 Email — {len(messages)} results for \"{query}\"\n")
        for msg in messages:
            print(format_email_summary(msg))
            print(f"         ID: {msg['id']}")
        print()
