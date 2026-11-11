from django import template
from ..models import Category, Tag

register = template.Library()


@register.simple_tag
def get_categories():
    """Get all categories with article count"""
    return Category.objects.all()


@register.simple_tag
def get_tags():
    """Get all tags"""
    return Tag.objects.all()


@register.simple_tag
def get_popular_tags(limit=10):
    """Get popular tags based on article count"""
    return Tag.objects.all()[:limit]
