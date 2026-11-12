"""500.html is rendered by django.views.defaults.server_error with no request context: no context
processors, no profile, no DB. These tests run without the django_db mark, so any query would fail."""
from django.template import loader
from django.test import RequestFactory
from django.views.defaults import server_error


def test_server_error_handler_renders_atlas_error_window():
    response = server_error(RequestFactory().get("/boom/"))
    html = response.content.decode()
    assert response.status_code == 500
    assert '<html lang="en" data-theme="green">' in html
    assert '<section class="at-win at-win--error is-active" aria-label="errors/500.log">' in html
    assert '<span class="at-win__title">errors/500.log</span>' in html
    assert "Error 500" in html and 'href="/"' in html
    assert "<style>" in html  # readable without the Vite bundle


def test_500_template_renders_with_empty_context():
    html = loader.get_template("500.html").render({})
    assert "errors/500.log" in html
