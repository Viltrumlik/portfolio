from django.urls import path
from .views import AboutView, SkillsView, ExperienceView

app_name = 'pages'

urlpatterns = [
    path('about/', AboutView.as_view(), name='about'),
    path('skills/', SkillsView.as_view(), name='skills'),
    path('experience/', ExperienceView.as_view(), name='experience'),
]
