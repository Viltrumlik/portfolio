from django.urls import path

from . import views

app_name = "integrations"

urlpatterns = [
    path("github/", views.github_webhook, name="github-webhook"),
]
