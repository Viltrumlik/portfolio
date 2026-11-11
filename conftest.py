"""Project-wide test setup: no real network, and plain static storage (no collectstatic needed)."""
import pytest

pytest_plugins = ["integrations.tests.fixtures"]


@pytest.fixture(autouse=True)
def _plain_static_storage(settings):
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
