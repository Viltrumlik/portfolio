import json

from django.template import Context, Template
from django.test import override_settings


def render(entry="src/main.ts"):
    return Template("{% load vite %}{% vite_asset entry %}").render(Context({"entry": entry}))


def test_missing_manifest_renders_nothing(tmp_path):
    with override_settings(VITE_MANIFEST_PATH=tmp_path / "nope.json", VITE_DEV_SERVER=""):
        assert render().strip() == ""


def test_built_entry_renders_module_script_and_css(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"src/main.ts": {"file": "assets/main-abc.js", "css": ["assets/main-def.css"], "isEntry": True}}))
    with override_settings(VITE_MANIFEST_PATH=manifest, VITE_DEV_SERVER="", STATIC_URL="/static/",
                           STORAGES={"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}):
        html = render()
    assert '<script type="module" src="/static/dist/assets/main-abc.js"></script>' in html
    assert '<link rel="stylesheet" href="/static/dist/assets/main-def.css">' in html


def test_dev_server_renders_client_and_entry():
    with override_settings(VITE_DEV_SERVER="http://localhost:5173"):
        html = render()
    assert 'src="http://localhost:5173/@vite/client"' in html
    assert 'src="http://localhost:5173/src/main.ts"' in html
