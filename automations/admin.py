from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Event, Rule, RuleRun


@admin.register(Event)
class EventAdmin(ModelAdmin):
    list_display = ("type", "source", "public", "occurred_at", "dispatched_at")
    list_filter = ("type", "source", "public")
    search_fields = ("type", "external_id")
    date_hierarchy = "occurred_at"


@admin.register(Rule)
class RuleAdmin(ModelAdmin):
    list_display = ("name", "trigger", "action", "is_enabled", "is_builtin", "run_count", "last_run_at")
    list_filter = ("is_enabled", "is_builtin", "action")
    readonly_fields = ("run_count", "last_run_at", "created_at")


@admin.register(RuleRun)
class RuleRunAdmin(ModelAdmin):
    list_display = ("rule", "event", "status", "ran_at")
    list_filter = ("status",)
