from django.urls import path
from .views import ProjectListView, ProjectDetailView, TechnologyProjectListView

app_name = 'portfolio'

urlpatterns = [
    path('', ProjectListView.as_view(), name='project_list'),
    path('<slug:slug>/', ProjectDetailView.as_view(), name='project_detail'),
    path('technology/<slug:slug>/', TechnologyProjectListView.as_view(), name='technology_projects'),
]
