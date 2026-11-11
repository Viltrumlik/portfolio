from django.contrib import admin
from django.db import models
from unfold.admin import ModelAdmin

from .models import Experience, Post, Profile, Project, Service, Skill, SocialLink, Tag


@admin.register(Profile)
class ProfileAdmin(ModelAdmin):
    list_display = ("name", "handle", "headline", "availability", "updated_at")

    def has_add_permission(self, request):
        return not Profile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SocialLink)
class SocialLinkAdmin(ModelAdmin):
    list_display = ("platform", "label", "url", "order")
    list_editable = ("order",)
    formfield_overrides = {models.URLField: {"assume_scheme": "https"}}


@admin.register(Experience)
class ExperienceAdmin(ModelAdmin):
    list_display = ("role", "company", "start_date", "end_date", "order")
    list_editable = ("order",)


@admin.register(Skill)
class SkillAdmin(ModelAdmin):
    list_display = ("name", "group", "order")
    list_filter = ("group",)
    list_editable = ("group", "order")
    search_fields = ("name",)


@admin.register(Service)
class ServiceAdmin(ModelAdmin):
    list_display = ("title", "order")
    list_editable = ("order",)


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = ("title", "status", "published_at", "body_format")
    list_filter = ("status", "body_format", "tags")
    search_fields = ("title", "excerpt", "body")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    date_hierarchy = "published_at"


@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    list_display = ("display_title", "repo_full_name", "kind", "featured", "hidden", "order")
    list_filter = ("featured", "hidden", "kind")
    list_editable = ("featured", "hidden", "order")
    search_fields = ("title", "repo_full_name", "summary")
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ("repo",)
