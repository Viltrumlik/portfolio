"""Admin for integrations. Credentials and webhook secrets are never displayed."""
from django import forms
from django.contrib import admin
from unfold.admin import ModelAdmin

from .crypto import mask
from .models import Connection, ContributionDay, InboundDelivery, ListeningSnapshot, OutboundHook, Repo, SyncRun

SECRET_KEYS = {"github": "token", "lastfm": "api_key", "telegram": "bot_token"}


@admin.register(Connection)
class ConnectionAdmin(ModelAdmin):
    list_display = ("provider", "status", "account", "last_synced_at", "error_code")
    list_filter = ("status",)
    exclude = ("credentials",)
    readonly_fields = ("masked_secret", "last_synced_at", "created_at", "updated_at")

    @admin.display(description="Secret")
    def masked_secret(self, obj):
        return mask((obj.credentials or {}).get(SECRET_KEYS.get(obj.provider, ""), "")) or "—"


@admin.register(Repo)
class RepoAdmin(ModelAdmin):
    list_display = ("full_name", "language", "stars", "pinned", "is_fork", "is_archived", "pushed_at")
    list_filter = ("pinned", "is_fork", "is_archived", "language")
    search_fields = ("full_name", "description")


@admin.register(ContributionDay)
class ContributionDayAdmin(ModelAdmin):
    list_display = ("date", "count", "level")
    date_hierarchy = "date"


@admin.register(ListeningSnapshot)
class ListeningSnapshotAdmin(ModelAdmin):
    list_display = ("track", "artist", "now_playing", "played_at", "fetched_at")


@admin.register(SyncRun)
class SyncRunAdmin(ModelAdmin):
    list_display = ("connection", "kind", "status", "items_changed", "started_at", "finished_at")
    list_filter = ("status", "kind")


@admin.register(InboundDelivery)
class InboundDeliveryAdmin(ModelAdmin):
    list_display = ("provider", "event", "delivery_id", "status", "received_at")
    list_filter = ("provider", "status", "event")
    search_fields = ("delivery_id",)


class OutboundHookForm(forms.ModelForm):
    url = forms.URLField(assume_scheme="https", max_length=200, help_text="An https URL (n8n, Make, Zapier).")
    new_secret = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Signing secret for X-Atlas-Signature. Leave empty to keep the current one.",
    )

    class Meta:
        model = OutboundHook
        exclude = ("secret",)

    def clean_url(self):
        url = self.cleaned_data["url"]
        if not url.startswith("https://"):
            raise forms.ValidationError("Webhook URLs must use https.")
        return url

    def save(self, commit=True):
        hook = super().save(commit=False)
        if self.cleaned_data.get("new_secret"):
            hook.secret = {"secret": self.cleaned_data["new_secret"]}
        if commit:
            hook.save()
        return hook


@admin.register(OutboundHook)
class OutboundHookAdmin(ModelAdmin):
    form = OutboundHookForm
    list_display = ("name", "url", "is_active", "last_status_code", "last_delivery_at")
    list_filter = ("is_active",)
    readonly_fields = ("masked_secret", "last_status_code", "last_delivery_at", "created_at")

    @admin.display(description="Current secret")
    def masked_secret(self, obj):
        return mask((obj.secret or {}).get("secret", "")) or "—"
