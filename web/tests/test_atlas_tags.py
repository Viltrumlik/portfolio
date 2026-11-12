import datetime as dt

import pytest
from django.template import Context, Template
from django.test import RequestFactory
from django.utils import timezone

from automations.models import Event
from content.models import Profile, Project
from integrations.models import ContributionDay, ListeningSnapshot, Repo

BAR = '<div class="at-win__bar"><span class="at-win__ctl" aria-hidden="true"><i></i><i></i><i></i></span>'


def render(src, context=None, request=None):
    ctx = dict(context or {})
    if request is not None:
        ctx["request"] = request
    return Template("{% load atlas %}" + src).render(Context(ctx))


# window --------------------------------------------------------------------------------


def test_window_renders_reference_markup():
    html = render('{% window title="about.md" active=True id="about" x="3%" y=20 w="46%" %}<p>Hi</p>{% endwindow %}')
    assert html == (
        '<section class="at-win is-active" data-win="about" aria-label="about.md" style="--x:3%;--y:20px;--w:46%">'
        + BAR + '<span class="at-win__title">about.md</span></div>'
        '<div class="at-win__body"><p>Hi</p></div></section>'
    )


def test_window_without_position_or_id():
    html = render('{% window title="contact.md" %}x{% endwindow %}')
    assert html.startswith('<section class="at-win" aria-label="contact.md">')


def test_window_bar_end_label_class_and_data_attrs():
    html = render(
        '{% window title="now.app" label="Now" cls="at-now" bar_end=end data_island="now" data_src="/api/live/now.json" %}'
        "{% endwindow %}",
        {"end": "<b>x</b>"},
    )
    assert '<section class="at-win at-now" aria-label="Now" data-island="now" data-src="/api/live/now.json">' in html
    assert '<span class="at-win__end">&lt;b&gt;x&lt;/b&gt;</span>' in html


def test_window_escapes_title_from_context():
    html = render("{% window title=t %}{% endwindow %}", {"t": '<script>"x"</script>'})
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


# primitives ------------------------------------------------------------------------------


def test_icon_matches_reference_svg():
    html = render('{% icon "arrow-right" size=14 %}')
    assert html == (
        '<svg class="at-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<path d="M4 12h15"/><path d="M13 6l6 6-6 6"/></svg>'
    )


def test_icon_with_title_is_an_image_and_circles_render():
    html = render('{% icon "alert" title="Failed" %}')
    assert 'role="img" aria-label="Failed"' in html
    assert 'aria-hidden' not in html
    assert '<circle cx="12" cy="12" r="8.5"/>' in html


def test_unknown_icon_renders_nothing():
    assert render('{% icon "nope" %}') == ""


def test_badge():
    html = render('{% badge "Syncing" tone="accent" dot=True pulse=True %}')
    assert html == '<span class="at-badge at-badge--accent"><span class="at-badge__dot is-pulse" aria-hidden="true"></span>Syncing</span>'
    assert render('{% badge "Pinned" %}') == '<span class="at-badge at-badge--neutral">Pinned</span>'


def test_button_as_link_and_as_submit():
    html = render('{% button "See my work" href="/work/" variant="primary" icon_right="arrow-right" %}')
    assert html.startswith('<a href="/work/" class="at-btn at-btn--primary"><span>See my work</span><svg class="at-icon" width="16"')
    html = render('{% button "Send message" type="submit" size="sm" %}')
    assert html == '<button type="submit" class="at-btn at-btn--secondary at-btn--sm"><span>Send message</span></button>'


def test_button_passes_data_attributes():
    html = render('{% button "Switch theme" variant="ghost" data_theme_toggle=True %}')
    assert '<button type="button" class="at-btn at-btn--ghost" data-theme-toggle>' in html


def test_kbd_and_service_code():
    assert render('{% kbd "⌘K" %}') == '<kbd class="at-kbd">⌘K</kbd>'
    assert render('{% service_code "GH" label="GitHub" size="sm" %}') == (
        '<span class="at-code at-code--sm" role="img" aria-label="GitHub" title="GitHub">GH</span>'
    )
    assert render('{% service_code "RS" %}') == '<span class="at-code at-code--md" aria-hidden="true">RS</span>'


def test_section_header_with_action():
    html = render('{% section_header title="Things I built" index="01" kicker="Selected work" action_label="All projects" action_href="/work/" %}')
    assert html.startswith(
        '<header class="at-section"><div class="at-section__meta"><span class="at-section__index">01</span>'
        '<span class="at-section__kicker">Selected work</span></div><div class="at-section__row">'
        '<h2 class="at-section__title" data-island="decode">Things I built</h2><a href="/work/" class="at-btn at-btn--ghost at-btn--sm">'
    )


def test_stat():
    html = render('{% stat value="14" label="Stars" unit="★" %}')
    assert html == (
        '<div class="at-stat"><div class="at-stat__value">14<span class="at-stat__unit">★</span></div>'
        '<div class="at-stat__label">Stars</div></div>'
    )


def test_dock():
    items = [{"code": "GH", "label": "Work", "href": "/work/"}, {"code": "RS", "label": "Feed", "href": "/feed", "active": True}]
    html = render("{% dock items %}", {"items": items})
    assert html == (
        '<nav class="at-dock" aria-label="Dock">'
        '<a href="/work/" class="at-dock__item" title="Work" aria-label="Work">GH</a>'
        '<a href="/feed" class="at-dock__item is-active" title="Feed" aria-label="Feed">RS</a></nav>'
    )


# data components -------------------------------------------------------------------------


@pytest.mark.django_db
def test_contribution_graph_is_omitted_without_data():
    assert render("{% contribution_graph %}").strip() == ""


@pytest.mark.django_db
def test_contribution_graph_from_rows():
    end = dt.date(2026, 11, 11)  # a Wednesday
    for i in range(30):
        ContributionDay.objects.create(date=end - dt.timedelta(days=i), count=i % 5)
    html = render("{% contribution_graph weeks=4 %}")
    assert html.startswith('<figure class="at-graph"><div class="at-graph__scroll"><svg')
    # 3 full weeks + Sunday..Wednesday of the last one
    assert html.count('<rect ') == 3 * 7 + 4
    total = sum(i % 5 for i in range(25))
    assert f'aria-label="{total} contributions in the last 4 weeks"' in html
    assert "at-heat-4" in html and "at-heat-0" in html
    assert "<title>4 contributions on Nov 7, 2026</title>" in html
    assert "<title>1 contribution on Nov 10, 2026</title>" in html
    assert '<span class="at-graph__legend" aria-hidden="true">Less<i class="at-heat-0"></i>' in html


@pytest.mark.django_db
def test_project_row_from_project():
    repo = Repo.objects.create(github_id=1, name="volunteers_bot", full_name="a/volunteers_bot", url="https://github.com/a/volunteers_bot", language="Python")
    p = Project.objects.create(repo_full_name="a/volunteers_bot", slug="volunteers-bot", title="Volunteers bot",
                               summary="Registers volunteers.", kind="Bot", stack=["aiogram", "Redis"], repo=repo)
    html = render("{% project_row p index=1 %}", {"p": p})
    assert html.startswith('<a class="at-prow" href="/work/volunteers-bot/"><span class="at-prow__index">01</span>')
    assert '<span class="at-prow__title">Volunteers bot</span><span class="at-prow__summary">Registers volunteers.</span>' in html
    assert '<span class="at-prow__stack">aiogram · Redis</span>' in html
    assert '<span class="at-prow__year">Bot<svg' in html


def test_project_row_from_kwargs_without_link():
    html = render('{% project_row title="A post" summary="Short" index=3 meta="Nov 2026" %}')
    assert html == (
        '<div class="at-prow"><span class="at-prow__index">03</span><span class="at-prow__main">'
        '<span class="at-prow__title">A post</span><span class="at-prow__summary">Short</span></span>'
        '<span class="at-prow__stack"></span><span class="at-prow__year">Nov 2026</span></div>'
    )


@pytest.mark.django_db
def test_repo_card():
    repo = Repo.objects.create(github_id=2, name="shop", full_name="a1/shop", url="https://github.com/a1/shop",
                               description="A shop.", language="Python", stars=3, forks=1, pinned=True,
                               pushed_at=timezone.now() - dt.timedelta(days=2))
    html = render("{% repo_card repo %}", {"repo": repo})
    assert html.startswith('<a class="at-repo" href="https://github.com/a1/shop">')
    assert '<span class="at-repo__name"><span class="at-repo__owner">a1/</span>shop</span><span class="at-badge at-badge--neutral">Pinned</span>' in html
    assert '<p class="at-repo__desc">A shop.</p>' in html
    assert '<span class="at-repo__lang"><i aria-hidden="true"></i>Python</span>' in html
    assert '3<span class="at-sr"> stars</span>' in html
    assert '<span class="at-repo__updated">2 days ago</span>' in html


@pytest.mark.django_db
def test_activity_feed_from_events():
    Event.objects.create(type="github.push", source="github", public=True,
                         payload={"repo": "a1/shop", "commits": 3, "branch": "main"},
                         occurred_at=timezone.now())
    Event.objects.create(type="sync.failed", source="lastfm", public=True, payload={"text": "Last.fm sync failed"})
    html = render("{% activity_feed events %}", {"events": Event.objects.all()})
    assert html.startswith('<ol class="at-feed" aria-label="Activity">')
    assert '<span class="at-code at-code--sm" role="img" aria-label="GitHub" title="GitHub">GH</span>' in html
    assert "Pushed 3 commits to a1/shop" in html
    assert '<span class="at-feed__meta">main</span>' in html
    assert '<li class="at-feed__row is-danger">' in html
    assert 'aria-label="Failed"' in html


@pytest.mark.django_db
def test_activity_feed_empty_renders_nothing():
    assert render("{% activity_feed events %}", {"events": []}) == ""


# site chrome -----------------------------------------------------------------------------


@pytest.mark.django_db
def test_menubar_marks_active_link_and_has_clock_and_cmdk():
    profile = Profile.load()
    profile.handle = "alisher.os"
    profile.location = "Fergana, Uzbekistan"
    profile.save()
    request = RequestFactory().get("/writing/some-post/")
    html = render("{% menubar %}", {"profile": profile}, request=request)
    assert '<header class="at-menubar">' in html
    assert '<a class="at-menubar__brand" href="/"><span class="at-menubar__logo" aria-hidden="true"></span>alisher.os</a>' in html
    assert '<a href="/writing/" class="at-menubar__link is-active" aria-current="page">Writing</a>' in html
    assert '<a href="/work/" class="at-menubar__link">Work</a>' in html
    assert '<span class="at-menubar__status"><i aria-hidden="true"></i>Available for work</span>' in html
    assert 'Fergana <time data-island="clock" data-tz="Asia/Tashkent" data-format="HH:MM">' in html
    assert 'data-cmdk-open' in html and '<kbd class="at-kbd">⌘K</kbd>' in html


@pytest.mark.django_db
def test_menubar_hides_status_when_availability_hidden():
    profile = Profile.load()
    profile.availability = Profile.Availability.HIDDEN
    profile.save()
    html = render("{% menubar %}", {"profile": profile}, request=RequestFactory().get("/"))
    assert "at-menubar__status" not in html


@pytest.mark.django_db
def test_now_window_without_listening_hides_row():
    profile = Profile.load()
    profile.location = "Fergana, Uzbekistan"
    profile.save()
    html = render('{% now_window id="now" x="52%" y=240 w="36%" %}', {"profile": profile})
    assert 'data-island="now" data-src="/api/live/now.json"' in html
    assert 'class="at-win at-now"' in html and 'data-win="now"' in html
    assert '<time data-island="clock" data-tz="Asia/Tashkent" data-format="HH:MM">' in html
    assert '<div class="at-now__row" data-now-row="listening" hidden>' in html
    assert "Fergana, Uzbekistan" in html and "UTC+5" in html


@pytest.mark.django_db
def test_now_window_shows_fresh_listening():
    ListeningSnapshot.objects.create(track="Teardrop", artist="Massive Attack", now_playing=True)
    html = render("{% now_window %}", {"profile": Profile.load()})
    assert '<div class="at-now__row" data-now-row="listening">' in html
    assert '<span data-now-field="track">Teardrop</span>' in html
    assert '<span data-now-field="artist">Massive Attack</span>' in html
    assert '<span data-now-field="played">Now playing</span>' in html


@pytest.mark.django_db
def test_now_window_ignores_stale_listening():
    snap = ListeningSnapshot.objects.create(track="Old", artist="X", now_playing=True)
    ListeningSnapshot.objects.filter(pk=snap.pk).update(fetched_at=timezone.now() - dt.timedelta(minutes=61))
    html = render("{% now_window %}", {"profile": Profile.load()})
    assert "Old" not in html
    assert 'data-now-row="listening" hidden' in html


def test_clock_tag_renders_server_time():
    html = render('{% clock "Asia/Tashkent" %}')
    now = timezone.now().astimezone(dt.timezone(dt.timedelta(hours=5)))
    assert html in (
        f'<time data-island="clock" data-tz="Asia/Tashkent" data-format="HH:MM">{now:%H:%M}</time>',
        f'<time data-island="clock" data-tz="Asia/Tashkent" data-format="HH:MM">{(now + dt.timedelta(minutes=1)):%H:%M}</time>',
    )


def test_window_takes_an_optional_height():
    html = render('{% window title="t.sys" id="t" x="2%" y=20 w="30%" h=250 %}x{% endwindow %}')
    assert 'style="--x:2%;--y:20px;--w:30%;--h:250px"' in html


@pytest.mark.django_db
def test_menubar_has_a_sound_toggle_that_starts_off():
    html = render("{% menubar %}", {"profile": Profile.load()}, request=RequestFactory().get("/"))
    assert '<button type="button" class="at-menubar__sound" data-sound-toggle aria-pressed="false"><span data-sound-label>Sound off</span></button>' in html
