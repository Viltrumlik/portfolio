import pytest
from django.test import RequestFactory

from content.context_processors import site


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("cookie", "expected"),
    [
        (None, "green"),
        ("green", "green"),
        ("amber", "amber"),
        ("ice", "ice"),
        ("dark", "green"),
        ("light", "green"),
        ('"><script>', "green"),
    ],
)
def test_theme_comes_from_the_cookie_and_falls_back_to_green(cookie, expected):
    request = RequestFactory().get("/")
    if cookie is not None:
        request.COOKIES["theme"] = cookie
    assert site(request)["theme"] == expected
