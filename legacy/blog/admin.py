from django.contrib import admin
from unfold.admin import ModelAdmin
from django_summernote.admin import SummernoteModelAdmin
from .models import Category, Tag, Article


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    ordering = ['name']


@admin.register(Article)
class ArticleAdmin(SummernoteModelAdmin, ModelAdmin):
    list_display = ['title', 'category', 'published', 'published_at', 'reading_time']
    list_filter = ['published', 'category', 'tags', 'published_at']
    search_fields = ['title', 'excerpt', 'content']
    list_editable = ['published']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    date_hierarchy = 'published_at'
    ordering = ['-published_at', '-created_at']
    summernote_fields = ('content',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'excerpt', 'category')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Media', {
            'fields': ('cover',)
        }),
        ('Tags', {
            'fields': ('tags',)
        }),
        ('Publication', {
            'fields': ('published', 'published_at')
        }),
    )
    
    readonly_fields = ['reading_time', 'created_at', 'updated_at']
