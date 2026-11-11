import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _isolated_cache_media_and_static(settings, tmp_path):
    """Each web test gets an empty cache (rate limits), its own MEDIA_ROOT (OG images), and plain static
    storage (the manifest storage needs `collectstatic`, which tests don't run)."""
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.SITE_URL = "https://guts.test"
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    cache.clear()
    yield
    cache.clear()
