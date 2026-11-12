import io
import re

import pytest
from django.conf import settings
from PIL import Image

from content.models import Post

from . import factories as f

pytestmark = pytest.mark.django_db


def meta(html, prop):
    m = re.search(rf'<meta (?:property|name)="{re.escape(prop)}" content="([^"]*)"', html)
    return m.group(1) if m else None


def test_home_has_canonical_and_open_graph(client):
    f.profile(name="Alisher M", headline="Backend developer")
    html = client.get("/").content.decode()
    assert '<link rel="canonical" href="https://guts.test/">' in html
    assert meta(html, "og:title") == "Alisher M"
    assert meta(html, "og:description") == "Backend developer"
    assert meta(html, "og:url") == "https://guts.test/"
    assert meta(html, "og:image") == "https://guts.test/og/page/home.png"
    assert meta(html, "twitter:card") == "summary_large_image"


def test_post_page_has_its_own_title_description_and_image(client):
    f.profile(name="Alisher M")
    f.post("clean-code", title="Writing clean code", excerpt="Habits that help.")
    html = client.get("/writing/clean-code/").content.decode()
    assert "<title>Writing clean code · Alisher M</title>" in html
    assert '<meta name="description" content="Habits that help.">' in html
    assert meta(html, "og:type") == "article"
    assert meta(html, "og:image") == "https://guts.test/og/post/clean-code.png"
    assert '<link rel="canonical" href="https://guts.test/writing/clean-code/">' in html


def test_project_page_meta(client):
    f.profile(name="Alisher M")
    f.project("shop", title="Django shop", summary="A shop for small stores.")
    html = client.get("/work/shop/").content.decode()
    assert "<title>Django shop · Alisher M</title>" in html
    assert meta(html, "og:image") == "https://guts.test/og/project/shop.png"
    assert meta(html, "og:description") == "A shop for small stores."


def test_sitemap_lists_pages_projects_and_posts(client):
    f.profile()
    f.project("shop")
    f.project("hidden", hidden=True)
    f.post("hello")
    f.post("draft", status=Post.Status.DRAFT)
    r = client.get("/sitemap.xml")
    assert r.status_code == 200
    xml = r.content.decode()
    for path in ("/", "/work/", "/writing/", "/about/", "/contact/", "/work/shop/", "/writing/hello/"):
        assert f"<loc>http://testserver{path}</loc>" in xml or f"<loc>https://guts.test{path}</loc>" in xml
    assert "/work/hidden/" not in xml and "/writing/draft/" not in xml


def test_robots_txt(client):
    r = client.get("/robots.txt")
    assert r.status_code == 200 and r["Content-Type"].startswith("text/plain")
    body = r.content.decode()
    assert "Disallow: /studio/" in body and "Disallow: /admin/" in body
    assert "Sitemap: https://guts.test/sitemap.xml" in body


def test_feed_has_published_posts_only(client):
    f.profile(name="Alisher M")
    f.post("hello", title="Hello world", excerpt="First post.")
    f.post("draft", title="Secret draft", status=Post.Status.DRAFT)
    r = client.get("/writing/feed.xml")
    assert r.status_code == 200 and "xml" in r["Content-Type"]
    xml = r.content.decode()
    assert "Hello world" in xml and "First post." in xml
    assert "Secret draft" not in xml


def test_og_image_is_a_matrix_card_and_cached(client):
    f.profile()
    f.post("hello", title="Hello world")
    r = client.get("/og/post/hello.png")
    assert r.status_code == 200 and r["Content-Type"] == "image/png"
    img = Image.open(io.BytesIO(b"".join(r.streaming_content))).convert("RGB")
    assert img.size == (1200, 630)
    assert sum(img.getpixel((5, 5))) < 45  # near-black desk
    colors = {c for _, c in img.getcolors(1200 * 630)}
    assert (0, 255, 65) in colors  # phosphor title bar
    assert (197, 248, 42) not in colors  # no v2 lime
    cached = list((settings.MEDIA_ROOT / "og" / "post").glob("hello-*.png"))
    assert len(cached) == 1
    mtime = cached[0].stat().st_mtime_ns
    client.get("/og/post/hello.png")
    assert cached[0].stat().st_mtime_ns == mtime


def test_og_image_for_pages_and_unknowns(client):
    f.profile()
    assert client.get("/og/page/home.png").status_code == 200
    assert client.get("/og/post/missing.png").status_code == 404
    assert client.get("/og/page/nowhere.png").status_code == 404
    assert client.get("/og/user/x.png").status_code == 404
    f.post("draft", status=Post.Status.DRAFT)
    assert client.get("/og/post/draft.png").status_code == 404
