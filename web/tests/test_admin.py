import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model

from content.models import Experience, Post, Profile, Project, Service, Skill, SocialLink, Tag
from web.models import ContactMessage

from . import factories as f

pytestmark = pytest.mark.django_db

MODELS = [Profile, SocialLink, Experience, Skill, Service, Tag, Post, Project, ContactMessage]


def test_content_models_and_messages_are_registered():
    for model in MODELS:
        assert admin.site.is_registered(model), model.__name__


def test_changelists_and_forms_load_for_superuser(client):
    f.profile()
    f.post("hello", tags=["Django"])
    f.project("shop")
    ContactMessage.objects.create(name="Dana", email="d@example.com", message="Hi")
    user = get_user_model().objects.create_superuser("owner", "owner@example.com", "x-test-pass")
    client.force_login(user)
    for model in MODELS:
        meta = model._meta
        assert client.get(f"/admin/{meta.app_label}/{meta.model_name}/").status_code == 200, meta.model_name
        assert client.get(f"/admin/{meta.app_label}/{meta.model_name}/add/").status_code in (200, 403), meta.model_name
    assert client.get(f"/admin/content/post/{Post.objects.get().pk}/change/").status_code == 200
