"""Every project and post has a picture: an uploaded one, or the generated Matrix card."""
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from content.models import Post, Project

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"


def png(name="shot.png"):
    buf = io.BytesIO()
    Image.new("RGB", (12, 8), (0, 255, 65)).save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


def test_a_project_without_an_image_uses_its_card():
    project = Project.objects.create(repo_full_name="a/bot", slug="bot")
    assert not project.has_image
    assert project.image_url == "/og/project/bot.png"


def test_an_uploaded_project_image_wins_over_the_card():
    project = Project.objects.create(repo_full_name="a/bot", slug="bot", image=png())
    assert project.has_image
    assert project.image_url.startswith("/media/projects/") and project.image_url.endswith(".png")


def test_a_post_cover_wins_over_the_card():
    post = Post.objects.create(title="Hello", slug="hello")
    assert post.image_url == "/og/post/hello.png" and not post.has_image
    post.cover = png("cover.png")
    post.save()
    assert post.has_image and post.image_url.startswith("/media/writing/")
