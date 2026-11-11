from content.rendering import excerpt, render_body, render_markdown, sanitize_html


def test_markdown_renders_allowed_tags():
    html = render_markdown("## Title\n\nSome **bold** and *em* with `code`.\n\n- one\n- two\n")
    assert "<h2>Title</h2>" in html
    assert "<strong>bold</strong>" in html
    assert "<em>em</em>" in html
    assert "<code>code</code>" in html
    assert "<li>one</li>" in html


def test_markdown_strips_scripts_and_event_handlers():
    html = render_markdown('Hi <script>alert(1)</script> <img src="x.png" onerror="alert(1)" alt="x">')
    assert "<script" not in html
    assert "onerror" not in html
    assert '<img src="x.png" alt="x">' in html


def test_links_keep_href_and_title_only():
    html = render_markdown('[site](https://example.com "Example")')
    assert '<a href="https://example.com" title="Example">site</a>' in html


def test_javascript_urls_are_removed():
    html = sanitize_html('<a href="javascript:alert(1)">x</a>')
    assert "javascript:" not in html


def test_fenced_code_and_tables():
    html = render_markdown("```\nprint('hi')\n```\n\n| a | b |\n|---|---|\n| 1 | 2 |\n")
    assert "<pre><code>" in html
    assert "<table>" in html and "<td>1</td>" in html


def test_h1_is_not_allowed_in_bodies():
    html = sanitize_html("<h1>Big</h1><h4>Small</h4>")
    assert "<h1>" not in html
    assert "<h4>Small</h4>" in html


def test_render_body_by_format():
    assert "<strong>x</strong>" in render_body("**x**", "markdown")
    html = render_body('<p onclick="x()">Hi</p><script>bad()</script>', "html")
    assert html == "<p>Hi</p>"


def test_excerpt_is_plain_text_of_first_paragraph():
    md = "I build **APIs** and bots.\n\nSecond paragraph."
    assert excerpt(md) == "I build APIs and bots."


def test_excerpt_truncates_words():
    assert excerpt("one two three four five", words=3) == "one two three…"
