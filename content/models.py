import math
import re

from django.db import models
from django.urls import reverse
from django.utils.html import strip_tags


class Profile(models.Model):
    """The site owner. A single row: use Profile.load()."""

    class Availability(models.TextChoices):
        AVAILABLE = "available", "Available for work"
        BUSY = "busy", "Busy"
        HIDDEN = "hidden", "Hidden"

    name = models.CharField(max_length=120, default="Alisher Muhammadaliyev")
    handle = models.CharField(max_length=60, default="alisher.os")
    headline = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True, help_text="Markdown")
    location = models.CharField(max_length=120, blank=True)
    timezone = models.CharField(max_length=60, default="Asia/Tashkent")
    email = models.EmailField(blank=True)
    availability = models.CharField(max_length=12, choices=Availability.choices, default=Availability.AVAILABLE)
    availability_note = models.CharField(max_length=120, blank=True)
    cv = models.FileField(upload_to="cv/", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class SocialLink(models.Model):
    platform = models.CharField(max_length=40)
    label = models.CharField(max_length=80, blank=True)
    url = models.URLField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.label or self.platform


class Experience(models.Model):
    company = models.CharField(max_length=200)
    role = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Markdown")
    location = models.CharField(max_length=120, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True, help_text="Empty = current")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "-start_date"]

    def __str__(self):
        return f"{self.role} · {self.company}"

    @property
    def is_current(self):
        return self.end_date is None


class Skill(models.Model):
    name = models.CharField(max_length=80)
    group = models.CharField(max_length=60, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["group", "order", "name"]

    def __str__(self):
        return self.name


class Service(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class Tag(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Post(models.Model):
    class Format(models.TextChoices):
        MARKDOWN = "markdown", "Markdown"
        HTML = "html", "HTML (migrated)"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    excerpt = models.TextField(blank=True)
    body = models.TextField(blank=True)
    body_format = models.CharField(max_length=10, choices=Format.choices, default=Format.MARKDOWN)
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    cover = models.FileField(upload_to="writing/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("web:post", args=[self.slug])

    @property
    def reading_minutes(self):
        words = len(re.findall(r"\w+", strip_tags(self.body)))
        return max(1, math.ceil(words / 220))


class Project(models.Model):
    """A project shown on the site. Created from a GitHub repo on sync; curated in the studio."""

    repo_full_name = models.CharField(max_length=300, unique=True, help_text="owner/name on GitHub")
    repo = models.OneToOneField("integrations.Repo", null=True, blank=True, on_delete=models.SET_NULL, related_name="project")
    slug = models.SlugField(max_length=220, unique=True)
    title = models.CharField(max_length=200, blank=True, help_text="Overrides the repo name")
    summary = models.TextField(blank=True, help_text="One sentence: what it does for whom")
    case_study = models.TextField(blank=True, help_text="Markdown")
    kind = models.CharField(max_length=40, blank=True, help_text="Bot, Platform, Android…")
    stack = models.JSONField(default=list, blank=True)
    featured = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.display_title

    def get_absolute_url(self):
        return reverse("web:project", args=[self.slug])

    @property
    def display_title(self):
        return self.title or self.repo_full_name.split("/")[-1]
