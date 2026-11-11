from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.core.paginator import Paginator
from .models import Project, Technology


class ProjectListView(ListView):
    model = Project
    template_name = 'portfolio/project_list.html'
    context_object_name = 'projects'
    paginate_by = 12
    
    def get_queryset(self):
        return Project.objects.filter(is_active=True).select_related().prefetch_related('technologies')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['technologies'] = Technology.objects.all()
        context['featured_projects'] = Project.objects.filter(is_featured=True, is_active=True)[:3]
        return context


class ProjectDetailView(DetailView):
    model = Project
    template_name = 'portfolio/project_detail.html'
    context_object_name = 'project'
    
    def get_queryset(self):
        return Project.objects.filter(is_active=True).select_related().prefetch_related('technologies')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get related projects (same technologies)
        project = context['project']  # Already fetched by DetailView
        related_projects = Project.objects.filter(
            technologies__in=project.technologies.all(),
            is_active=True
        ).exclude(id=project.id).distinct()[:3]
        context['related_projects'] = related_projects
        return context


class TechnologyProjectListView(ListView):
    model = Project
    template_name = 'portfolio/technology_projects.html'
    context_object_name = 'projects'
    paginate_by = 12
    
    def get_queryset(self):
        technology_slug = self.kwargs['slug']
        technology = get_object_or_404(Technology, slug=technology_slug)
        return Project.objects.filter(
            technologies=technology,
            is_active=True
        ).select_related().prefetch_related('technologies')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        technology_slug = self.kwargs['slug']
        context['technology'] = get_object_or_404(Technology, slug=technology_slug)
        context['technologies'] = Technology.objects.all()
        return context
