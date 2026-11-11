from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Job


@admin.register(Job)
class JobAdmin(ModelAdmin):
    list_display = ("kind", "status", "run_at", "attempts", "max_attempts", "finished_at")
    list_filter = ("status", "kind")
    search_fields = ("kind", "dedupe_key", "last_error")
    readonly_fields = ("locked_at", "finished_at", "created_at")
    date_hierarchy = "run_at"
