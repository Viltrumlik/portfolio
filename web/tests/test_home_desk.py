"""The Matrix home desk and the public layout chrome (rain, boot screen, sound toggle)."""
import pytest

from automations.models import Event
from content.models import Skill, SocialLink

from . import factories as f
from .test_pages import html_of

pytestmark = pytest.mark.django_db


def test_desk_windows_carry_their_layout_size(client):
    f.profile()
    html = html_of(client.get("/"))
    assert 'data-win="about" aria-label="about.sys" style="--x:2%;--y:20px;--w:37%;--h:350px;--delay:0ms"' in html
    assert 'data-win="terminal" aria-label="terminal — tty1" style="--x:40.5%;--y:20px;--w:33%;--h:250px;--delay:70ms"' in html


def test_about_window_decodes_the_handle(client):
    f.profile()
    html = html_of(client.get("/"))
    assert 'data-island="decode" data-decode="load" data-decode-repeat="9000">' in html


def test_terminal_types_the_real_transcript(client):
    f.profile()
    f.project("atlas")
    f.project("shop")
    html = html_of(client.get("/"))
    assert '<pre class="at-term" data-island="typer" data-loop="5000" data-max-lines="9">$ whoami\n' in html
    assert "$ ls ~/projects | wc -l\n2\n" in html


def test_projects_window_lists_featured_projects_like_ls(client):
    f.profile()
    f.project("volunteers-bot", featured=True, kind="Bot")
    html = html_of(client.get("/"))
    assert 'aria-label="projects/"' in html
    assert '<a class="at-ls__row" href="/work/volunteers-bot/">' in html
    assert '<span class="at-ls__name">volunteers-bot/</span>' in html


def test_projects_window_shows_stars_or_falls_back_to_the_kind(client):
    f.profile()
    f.project("starred", featured=True, kind="Platform", repo=f.repo("starred", stars=3))
    f.project("unstarred", featured=True, kind="Game", repo=f.repo("unstarred", stars=0))
    html = html_of(client.get("/"))
    assert '<span class="at-ls__meta">★ 3</span>' in html
    assert '<span class="at-ls__meta">game</span>' in html
    assert "★ 0" not in html


def test_stack_cfg_and_links_windows_show_only_with_data(client):
    f.profile()
    html = html_of(client.get("/"))
    assert 'aria-label="stack.cfg"' not in html and 'aria-label="links.sh"' not in html
    Skill.objects.create(group="Backend", name="Django")
    SocialLink.objects.create(platform="GitHub", url="https://github.com/example")
    html = html_of(client.get("/"))
    assert 'aria-label="stack.cfg"' in html and "[backend]" in html and "Django" in html
    assert 'aria-label="links.sh"' in html and 'href="https://github.com/example"' in html


def test_activity_feed_window_needs_public_events(client):
    f.profile()
    assert 'aria-label="activity.feed"' not in html_of(client.get("/"))
    Event.objects.create(type="github.push", source="github", public=True, payload={"repo": "a1/shop", "commits": 2})
    assert 'aria-label="activity.feed"' in html_of(client.get("/"))


def test_sys_info_counts_projects(client):
    f.profile()
    f.project("one")
    html = html_of(client.get("/"))
    assert 'aria-label="sys.info"' in html
    assert '<div class="at-stat__value">1</div><div class="at-stat__label">Projects</div>' in html


def test_public_layout_has_rain_boot_screen_and_sound_toggle(client):
    f.profile()
    html = html_of(client.get("/about/"))
    assert '<canvas data-island="rain" class="fx-rain" aria-hidden="true"></canvas>' in html
    assert 'data-island="bootscreen" class="fx-boot"' in html
    assert 'data-sound-toggle aria-pressed="false"><span data-sound-label>Sound off</span></button>' in html


def test_studio_has_no_rain_or_boot_screen(client):
    f.profile()
    response = client.get("/studio/login/")
    html = response.content.decode()
    assert response.status_code == 200
    assert "fx-rain" not in html and "fx-boot" not in html
