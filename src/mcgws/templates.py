"""HTML email template for briefings."""

import re


def text_to_html(text: str) -> str:
    """Convert Claude's plain text output to simple HTML.

    Handles: ## headers, **bold**, - bullets, `code`, paragraphs.
    """
    lines = text.split("\n")
    html_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        # Empty line — close list if open, add paragraph break
        if not stripped:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("")
            continue

        # Headers
        if stripped.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            content = stripped[4:]
            html_lines.append(
                f'<h3 style="color:#4DAAAA;margin:16px 0 8px 0;">'
                f"{content}</h3>"
            )
            continue
        if stripped.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            content = stripped[3:]
            html_lines.append(
                f'<h2 style="color:#4DAAAA;margin:20px 0 8px 0;'
                f'border-bottom:1px solid #4DAAAA;padding-bottom:4px;">'
                f"{content}</h2>"
            )
            continue

        # Bullet points
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_lines.append(
                    '<ul style="margin:8px 0;padding-left:20px;">'
                )
                in_list = True
            content = stripped[2:]
            content = _inline_format(content)
            html_lines.append(f"<li>{content}</li>")
            continue

        # Regular line
        if in_list:
            html_lines.append("</ul>")
            in_list = False
        formatted = _inline_format(stripped)
        html_lines.append(f'<p style="margin:6px 0;">{formatted}</p>')

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def _inline_format(text: str) -> str:
    """Apply inline formatting: **bold**, `code`."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(
        r"`(.+?)`",
        r'<code style="background:#e8e8e8;padding:1px 4px;'
        r'border-radius:3px;font-size:13px;">\1</code>',
        text,
    )
    return text


def wrap_briefing_html(body_text: str, command_type: str, date_str: str) -> str:
    """Wrap briefing text in an HTML email template.

    Args:
        body_text: Claude's plain text briefing output.
        command_type: e.g. "Morning Briefing", "Midday Check-in".
        date_str: e.g. "Thu Mar 6".

    Returns:
        Complete HTML document string.
    """
    body_html = text_to_html(body_text)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap');
</style>
</head>
<body style="margin:0;padding:0;background:#F8F9FA;font-family:Montserrat,Helvetica,Arial,sans-serif;color:#1A1A2E;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F8F9FA;">
<tr><td align="center" style="padding:24px 16px;">
<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);">

<!-- Header -->
<tr><td style="background:#4DAAAA;padding:20px 32px;">
<span style="font-family:Montserrat,Helvetica,Arial,sans-serif;font-size:20px;font-weight:700;color:#ffffff;letter-spacing:0.5px;">{command_type}</span>
<br>
<span style="font-family:Montserrat,Helvetica,Arial,sans-serif;font-size:13px;font-weight:300;color:rgba(255,255,255,0.85);">{date_str}</span>
</td></tr>

<!-- Body -->
<tr><td style="padding:24px 32px;font-size:14px;line-height:1.6;">
{body_html}
</td></tr>

<!-- Footer -->
<tr><td style="padding:16px 32px;border-top:1px solid #e8e8e8;font-size:11px;color:#888;">
Chief of Staff &middot; MehtaCognition
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""
