"""Pictures on the public pages: thumbnails in lists, a screenshot on detail pages when one is uploaded."""
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from . import factories as f
from .test_pages import html_of

pytestmark = pytest.mark.django_db


def png(name="shot.png", size=(120, 63)):
    buf = io.BytesIO()
    Image.new("RGB", size, (0, 255, 65)).save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


def test_work_list_shows_a_thumbnail_for_every_project(client):
    f.profile()
    f.project("shop")
    f.project("mars", image=png())
    html = html_of(client.get("/work/"))
    assert '<img class="at-prow__thumb" src="/og/project/shop.png" alt="" loading="lazy"' in html
    assert '<img class="at-prow__thumb" src="/media/projects/shot' in html
    assert html.count('class="at-prow at-prow--media"') == 2


def test_project_page_shows_the_screenshot_only_when_uploaded(client):
    f.profile()
    f.project("shop")
    f.project("mars", title="Zero to Mars", image=png(size=(120, 63)))
    assert "at-shot" not in html_of(client.get("/work/shop/"))
    html = html_of(client.get("/work/mars/"))
    assert '<img class="at-shot" src="/media/projects/shot' in html
    assert 'alt="Screenshot of Zero to Mars" width="120" height="63"' in html


def test_writing_list_and_post_show_covers(client):
    f.profile()
    f.post("plain", title="Plain")
    f.post("covered", title="Covered", cover=png("cover.png", size=(40, 21)))
    html = html_of(client.get("/writing/"))
    assert '<img class="at-prow__thumb" src="/og/post/plain.png" alt=""' in html
    assert '<img class="at-prow__thumb" src="/media/writing/cover' in html
    assert "at-shot" not in html_of(client.get("/writing/plain/"))
    assert '<img class="at-shot" src="/media/writing/cover' in html_of(client.get("/writing/covered/"))


def test_open_graph_uses_an_uploaded_image(client):
    f.profile()
    f.project("mars", image=png())
    html = client.get("/work/mars/").content.decode()
    assert 'property="og:image" content="https://guts.test/media/projects/shot' in html
