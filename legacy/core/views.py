from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib import messages
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings
from django.http import JsonResponse
from .models import SiteSetting, ContactMessage


class HomePageView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get featured projects
        from portfolio.models import Project
        context['featured_projects'] = Project.objects.filter(
            is_featured=True,
            is_active=True
        )[:6]

        # Get latest blog articles
        from blog.models import Article
        context['latest_articles'] = Article.objects.filter(
            published=True
        )[:3]

        # Get skills for homepage and group them
        from pages.models import Skill, AboutSection, Service, Experience
        context['skills'] = Skill.objects.all().order_by('group', 'order', 'name')
        about = AboutSection.get_singleton()
        context['about_section'] = about
        context['services'] = Service.objects.all().prefetch_related('features')
        context['experiences'] = Experience.objects.all().order_by('-start_date', 'order')[:2]

        skills_by_group = {}
        for skill in context['skills']:
            group = skill.get_group_display()
            skills_by_group.setdefault(group, []).append(skill)
        context['skills_by_group'] = skills_by_group

        # Numeric hero stats (for count-up animation)
        from portfolio.models import Technology
        def _digits(s, default=0):
            d = ''.join(ch for ch in str(s) if ch.isdigit())
            return int(d) if d else default
        context['stat_projects'] = Project.objects.filter(is_active=True).count()
        context['stat_years'] = _digits(about.years_experience, 2)
        context['stat_tech'] = Technology.objects.count()

        return context


def _save_and_notify(name, email, subject, message):
    """Persist a contact message and try (optionally) to email a notification.

    The message is always saved to the database, so it is never lost even when
    SMTP is not configured. Email delivery is best-effort and never raises.
    """
    contact = ContactMessage.objects.create(
        name=name, email=email, subject=subject, message=message,
    )

    if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
        try:
            site_settings = SiteSetting.get_singleton()
            recipient = site_settings.contact_email or settings.EMAIL_HOST_USER
            send_mail(
                subject=f"[Portfolio] {subject or 'New message'} — from {name}",
                message=f"From: {name} <{email}>\n\n{message}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=True,
            )
            contact.emailed = True
            contact.save(update_fields=['emailed'])
        except Exception:
            # Never let an email failure break the user's submission.
            pass

    return contact


class ContactFormView(TemplateView):
    template_name = 'core/contact.html'

    def post(self, request, *args, **kwargs):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        # Validation
        error = None
        if not (name and email and message):
            error = 'Please fill in your name, email, and message.'
        else:
            try:
                validate_email(email)
            except ValidationError:
                error = 'Please enter a valid email address.'

        if error:
            if is_ajax:
                return JsonResponse({'success': False, 'message': error})
            messages.error(request, error)
            return self.get(request, *args, **kwargs)

        _save_and_notify(name, email, subject, message)
        success_msg = "Thanks! Your message has been received — I'll get back to you soon."

        if is_ajax:
            return JsonResponse({'success': True, 'message': success_msg})

        messages.success(request, success_msg)
        return redirect(request.path)
