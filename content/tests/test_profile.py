import pytest

from content.models import Profile

pytestmark = pytest.mark.django_db


def test_load_returns_one_shared_profile():
    first = Profile.load()
    first.headline = "Backend developer"
    first.save()
    assert Profile.load().headline == "Backend developer"
    assert Profile.objects.count() == 1
