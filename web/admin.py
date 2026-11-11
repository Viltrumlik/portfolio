from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(ModelAdmin):
    list_display = ("name", "email", "created_at", "is_read")
    list_filter = ("is_read",)
    list_editable = ("is_read",)
    search_fields = ("name", "email", "message")
    readonly_fields = ("name", "email", "message", "ip_hash", "created_at")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False
