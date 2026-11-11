import pytest

from . import factories as f

pytestmark = pytest.mark.django_db

CSP = (
    "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; "
    "base-uri 'self'; form-action 'self'"
)


def test_public_pages_send_content_security_policy(client, settings):
    settings.VITE_DEV_SERVER = ""
    f.profile()
    r = client.get("/")
    assert r["Content-Security-Policy"] == CSP
    assert "camera=()" in r["Permissions-Policy"]


def test_vite_dev_server_is_allowed_for_scripts_and_hmr(client, settings):
    settings.VITE_DEV_SERVER = "http://localhost:5173/"
    f.profile()
    csp = client.get("/").headers["Content-Security-Policy"]
    assert "script-src 'self' http://localhost:5173;" in csp
    assert "connect-src 'self' http://localhost:5173 ws:;" in csp


def test_admin_keeps_its_own_scripts(client):
    r = client.get("/admin/login/")
    assert "Content-Security-Policy" not in r
