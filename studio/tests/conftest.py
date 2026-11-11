import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache

from integrations.tests.fixtures import api, no_network, resolve_to  # noqa: F401

PASSWORD = "correct horse battery staple"


@pytest.fixture(autouse=True)
def _studio_settings(settings, tmp_path):
    """Empty cache (login rate limit), a fixed SITE_URL and a throwaway MEDIA_ROOT for every studio test."""
    settings.SITE_URL = "https://guts.test"
    settings.MEDIA_ROOT = tmp_path / "media"
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def owner(db):
    return get_user_model().objects.create_user("owner", "owner@example.com", PASSWORD, is_staff=True)


@pytest.fixture
def member(db):
    return get_user_model().objects.create_user("member", "member@example.com", PASSWORD)


@pytest.fixture
def staff(client, owner):
    """A test client logged in as the (staff) owner."""
    client.force_login(owner)
    return client
