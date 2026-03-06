from mcgws.templates import wrap_briefing_html, text_to_html


def test_wrap_briefing_html_contains_body():
    html = wrap_briefing_html("Hello world", "Morning Briefing", "Thu Mar 6")
    assert "Hello world" in html
    assert "Morning Briefing" in html
    assert "Thu Mar 6" in html


def test_wrap_briefing_html_has_brand_colors():
    html = wrap_briefing_html("Test", "Briefing", "Mon Mar 9")
    assert "#4DAAAA" in html
    assert "Montserrat" in html


def test_wrap_briefing_html_is_valid_html():
    html = wrap_briefing_html("Test", "Briefing", "Mon Mar 9")
    assert html.startswith("<!DOCTYPE html>")
    assert "</html>" in html


def test_text_to_html_converts_headers():
    result = text_to_html("## Calendar\nEvent 1")
    assert "<h2 " in result
    assert "Calendar" in result


def test_text_to_html_converts_bold():
    result = text_to_html("**The One Thing:** Focus today")
    assert "<strong>" in result


def test_text_to_html_converts_bullets():
    result = text_to_html("- Item one\n- Item two")
    assert "<li>" in result


def test_text_to_html_converts_code():
    result = text_to_html("Run `g calendar today`")
    assert "<code " in result


def test_text_to_html_preserves_emoji():
    result = text_to_html("📅 Calendar")
    assert "📅" in result


def test_text_to_html_converts_paragraphs():
    result = text_to_html("Paragraph one.\n\nParagraph two.")
    assert "<p " in result
