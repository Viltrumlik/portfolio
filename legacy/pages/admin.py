from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Skill, Experience, AboutSection, Service, ServiceFeature


@admin.register(Skill)
class SkillAdmin(ModelAdmin):
    list_display = ['name', 'group', 'level', 'order']
    list_filter = ['group']
    search_fields = ['name', 'group']
    list_editable = ['level', 'order']
    ordering = ['group', 'order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'group', 'level')
        }),
        ('Display', {
            'fields': ('icon_class', 'order')
        }),
    )


@admin.register(Experience)
class ExperienceAdmin(ModelAdmin):
    list_display = ['company', 'role', 'start_date', 'end_date', 'is_current']
    list_filter = ['is_current']
    search_fields = ['company', 'role']


@admin.register(AboutSection)
class AboutSectionAdmin(ModelAdmin):
    list_display = ['title']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title',)
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Personal Information', {
            'fields': ('education', 'location', 'years_experience')
        }),
        ('Statistics', {
            'fields': ('projects_completed', 'happy_clients')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not AboutSection.objects.exists()


class ServiceFeatureInline(TabularInline):
    model = ServiceFeature
    extra = 1


@admin.register(Service)
class ServiceAdmin(ModelAdmin):
    list_display = ['title', 'order']
    list_editable = ['order']
    inlines = [ServiceFeatureInline]
