from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .site import published_posts, visible_projects


class _SiteUrl(Sitemap):
    """Absolute URLs on settings.SITE_URL, not on whatever Host header the request carried."""

    def get_domain(self, site=None):
        return urlsplit(settings.SITE_URL).netloc

    def get_protocol(self, protocol=None):
        return urlsplit(settings.SITE_URL).scheme or "https"


class PagesSitemap(_SiteUrl):
    changefreq = "weekly"

    def items(self):
        return ["web:home", "web:work", "web:writing", "web:about", "web:contact"]

    def location(self, item):
        return reverse(item)


class ProjectsSitemap(_SiteUrl):
    changefreq = "monthly"

    def items(self):
        return visible_projects().order_by("order", "pk")

    def lastmod(self, obj):
        return obj.updated_at


class PostsSitemap(_SiteUrl):
    changefreq = "monthly"

    def items(self):
        return published_posts()

    def lastmod(self, obj):
        return obj.updated_at


SITEMAPS = {"pages": PagesSitemap, "projects": ProjectsSitemap, "posts": PostsSitemap}
