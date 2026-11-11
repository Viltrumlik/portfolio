from django.contrib.sitemaps.views import sitemap
from django.urls import path

from . import views
from .feeds import LatestPostsFeed
from .sitemaps import SITEMAPS

app_name = "web"

urlpatterns = [
    path("", views.home, name="home"),
    path("work/", views.work, name="work"),
    path("work/<slug:slug>/", views.project, name="project"),
    path("writing/", views.writing, name="writing"),
    path("writing/feed.xml", LatestPostsFeed(), name="feed"),
    path("writing/tag/<slug:slug>/", views.writing_tag, name="tag"),
    path("writing/<slug:slug>/", views.post, name="post"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("api/live/now.json", views.live_now, name="live_now"),
    path("api/live/activity.json", views.live_activity, name="live_activity"),
    path("og/<str:kind>/<slug:slug>.png", views.og_image, name="og"),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("robots.txt", views.robots, name="robots"),
]
