from django.db import models
from django.urls import reverse
from django.utils.text import slugify


DEFAULT_SITE = {
    'site_name': 'Alex Morgan',
    'hero_title': "I'm Alex Morgan",
    'hero_subtitle': 'Full-Stack Developer',
    'hero_greeting': '👋 Hello, I am',
    'hero_description': "I build clean, scalable web applications with a focus on great user "
                        "experiences and reliable backend systems.",
    'contact_email': 'hello@example.com',
    'phone': '',
    'location': 'Remote · Worldwide',
}


class SiteSetting(models.Model):
    site_name = models.CharField(max_length=200, default=DEFAULT_SITE['site_name'])
    hero_title = models.CharField(max_length=500, default=DEFAULT_SITE['hero_title'])
    hero_subtitle = models.CharField(max_length=500, default=DEFAULT_SITE['hero_subtitle'])
    hero_greeting = models.CharField(max_length=100, default=DEFAULT_SITE['hero_greeting'])
    hero_description = models.TextField(default=DEFAULT_SITE['hero_description'])
    contact_email = models.EmailField(default=DEFAULT_SITE['contact_email'])
    phone = models.CharField(max_length=50, blank=True, default='', help_text="Optional public phone number")
    location = models.CharField(max_length=200, blank=True, default=DEFAULT_SITE['location'])
    logo = models.FileField(upload_to='core/', blank=True, null=True)
    favicon = models.FileField(upload_to='core/', blank=True, null=True)
    cv = models.FileField(upload_to='cv/', blank=True, null=True)

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.site_name

    @classmethod
    def get_singleton(cls):
        obj, created = cls.objects.get_or_create(pk=1, defaults=DEFAULT_SITE)
        return obj


class SocialLink(models.Model):
    PLATFORM_CHOICES = [
        ('discord', 'Discord'),
        ('linkedin', 'LinkedIn'),
        ('github', 'GitHub'),
        ('instagram', 'Instagram'),
        ('telegram', 'Telegram'),
        ('twitter', 'Twitter'),
        ('facebook', 'Facebook'),
        ('youtube', 'YouTube'),
    ]
    
    platform_name = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    url = models.URLField()
    icon_class = models.CharField(max_length=100, help_text="Font Awesome icon class")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = "Social Link"
        verbose_name_plural = "Social Links"
    
    def __str__(self):
        return f"{self.get_platform_name_display()} - {self.url}"


class SEO(models.Model):
    page_key = models.CharField(max_length=100, unique=True, help_text="Unique identifier for the page")
    meta_title = models.CharField(max_length=200)
    meta_description = models.TextField(max_length=500)
    meta_keywords = models.CharField(max_length=500, blank=True)
    og_image = models.FileField(upload_to='seo/', blank=True, null=True)
    
    class Meta:
        verbose_name = "SEO Metadata"
        verbose_name_plural = "SEO Metadata"
    
    def __str__(self):
        return f"{self.page_key} - {self.meta_title}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    emailed = models.BooleanField(default=False, help_text="Whether a notification email was sent")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"{self.name} <{self.email}> — {self.subject or 'No subject'}"
