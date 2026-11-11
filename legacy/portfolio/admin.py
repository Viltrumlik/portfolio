from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Technology, Project


@admin.register(Technology)
class TechnologyAdmin(ModelAdmin):
    list_display = ['name', 'icon_class']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    list_display = ['title', 'is_featured', 'is_active', 'created_at']
    list_filter = ['is_featured', 'is_active', 'technologies', 'created_at']
    search_fields = ['title', 'short_description', 'description']
    list_editable = ['is_featured', 'is_active']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['technologies']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'short_description', 'description')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Links', {
            'fields': ('github_url', 'live_url')
        }),
        ('Technologies', {
            'fields': ('technologies',)
        }),
        ('Settings', {
            'fields': ('is_featured', 'is_active')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
