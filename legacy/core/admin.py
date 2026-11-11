from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import SiteSetting, SocialLink, SEO, ContactMessage


@admin.register(SiteSetting)
class SiteSettingAdmin(ModelAdmin):
    list_display = ['site_name', 'contact_email']
    fieldsets = (
        ('Basic Information', {
            'fields': ('site_name', 'hero_title', 'hero_subtitle', 'hero_greeting', 'hero_description')
        }),
        ('Contact Details', {
            'fields': ('contact_email', 'phone', 'location')
        }),
        ('Media', {
            'fields': ('logo', 'favicon', 'cv')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not SiteSetting.objects.exists()


@admin.register(SocialLink)
class SocialLinkAdmin(ModelAdmin):
    list_display = ['platform_name', 'url', 'order', 'is_active']
    list_filter = ['platform_name', 'is_active']
    search_fields = ['platform_name', 'url']
    list_editable = ['order', 'is_active']
    ordering = ['order']


@admin.register(SEO)
class SEOAdmin(ModelAdmin):
    list_display = ['page_key', 'meta_title']
    search_fields = ['page_key', 'meta_title', 'meta_description']
    list_filter = ['page_key']
    fieldsets = (
        ('Basic SEO', {
            'fields': ('page_key', 'meta_title', 'meta_description')
        }),
        ('Advanced SEO', {
            'fields': ('meta_keywords', 'og_image'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ContactMessage)
class ContactMessageAdmin(ModelAdmin):
    list_display = ['name', 'email', 'subject', 'created_at', 'is_read', 'emailed']
    list_filter = ['is_read', 'emailed', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    list_editable = ['is_read']
    readonly_fields = ['name', 'email', 'subject', 'message', 'created_at', 'emailed']
    date_hierarchy = 'created_at'
    actions = ['mark_as_read', 'mark_as_unread']

    def has_add_permission(self, request):
        return False

    @admin.action(description="Mark selected messages as read")
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description="Mark selected messages as unread")
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
