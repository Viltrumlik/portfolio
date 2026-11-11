from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.sitemaps import Sitemap
from .models import Skill, Experience, AboutSection, Service


class AboutView(TemplateView):
    template_name = 'pages/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['about_section'] = AboutSection.get_singleton()
        context['skills'] = Skill.objects.all().order_by('group', 'order', 'name')
        context['experiences'] = Experience.objects.all().order_by('-start_date', 'order')
        context['services'] = Service.objects.all().prefetch_related('features').order_by('order')
        
        # Group skills by category
        skills_by_group = {}
        for skill in context['skills']:
            group = skill.get_group_display()
            if group not in skills_by_group:
                skills_by_group[group] = []
            skills_by_group[group].append(skill)
        context['skills_by_group'] = skills_by_group
        
        return context


class SkillsView(TemplateView):
    template_name = 'pages/skills.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['skills'] = Skill.objects.all().order_by('group', 'order', 'name')
        
        # Group skills by category
        skills_by_group = {}
        for skill in context['skills']:
            group = skill.get_group_display()
            if group not in skills_by_group:
                skills_by_group[group] = []
            skills_by_group[group].append(skill)
        context['skills_by_group'] = skills_by_group
        
        return context


class ExperienceView(TemplateView):
    template_name = 'pages/experience.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['experiences'] = Experience.objects.all().order_by('-start_date', 'order')
        return context


class StaticSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.8
    
    def items(self):
        return ['home', 'about', 'skills', 'experience', 'projects', 'blog']
    
    def location(self, item):
        if item == 'home':
            return '/'
        return f'/{item}/'


class PortfolioSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9
    
    def items(self):
        from portfolio.models import Project
        return Project.objects.filter(is_active=True)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return obj.get_absolute_url()


class BlogSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.7
    
    def items(self):
        from blog.models import Article
        return Article.objects.filter(published=True)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return obj.get_absolute_url()
