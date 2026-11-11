from django.contrib.syndication.views import Feed

from content.models import Profile
from content.rendering import excerpt

from .site import published_posts


class LatestPostsFeed(Feed):
    link = "/writing/"

    def title(self):
        return f"{Profile.load().name} · Writing"

    def description(self):
        return Profile.load().headline or "Writing"

    def items(self):
        return published_posts().prefetch_related("tags")[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt or excerpt(item.body, words=60, body_format=item.body_format)

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.published_at

    def item_updateddate(self, item):
        return item.updated_at

    def item_categories(self, item):
        return [t.name for t in item.tags.all()]
