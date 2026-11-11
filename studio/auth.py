"""Studio access: staff-only views and an owner login limited to 5 failures per 15 minutes per IP."""
import hashlib
from functools import wraps

from django import forms
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import redirect_to_login
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.views.decorators.cache import never_cache

from .forms import style

LOGIN_FAILURE_LIMIT = 5
LOGIN_WINDOW_SECONDS = 15 * 60
TOO_MANY = "Too many failed sign-ins from your network. Try again in 15 minutes."


def staff_required(view):
    """Anonymous → the login page; signed in but not staff → 403. Responses are never cached."""

    @wraps(view)
    def wrapped(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return never_cache(wrapped)


def client_ip(request):
    """nginx sets X-Real-IP; without it (local runs) use REMOTE_ADDR."""
    return request.META.get("HTTP_X_REAL_IP", "").strip() or request.META.get("REMOTE_ADDR", "") or "unknown"


def _failures_key(request):
    digest = hashlib.sha256(f"{settings.SECRET_KEY}:{client_ip(request)}".encode()).hexdigest()
    return f"studio:login-failures:{digest}"


def _count_failure(key):
    if not cache.add(key, 1, LOGIN_WINDOW_SECONDS):
        try:
            cache.incr(key)
        except ValueError:  # expired between add and incr
            cache.set(key, 1, LOGIN_WINDOW_SECONDS)


class OwnerLoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "That username and password don’t match. Check both and try again.",
        "inactive": "This account can’t open the studio. Sign in with the owner account.",
    }

    def __init__(self, *args, locked=False, **kwargs):
        self.locked = locked
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Username"
        self.fields["password"].label = "Password"
        style(self)

    def clean(self):
        if self.locked:  # refuse before checking the password
            raise forms.ValidationError(TOO_MANY, code="rate_limited")
        return super().clean()

    def confirm_login_allowed(self, user):
        if not (user.is_active and user.is_staff):
            raise forms.ValidationError(self.error_messages["inactive"], code="inactive")


class LoginView(auth_views.LoginView):
    template_name = "studio/login.html"
    authentication_form = OwnerLoginForm
    redirect_authenticated_user = True

    locked = False

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "locked": self.locked}

    def post(self, request, *args, **kwargs):
        key = _failures_key(request)
        self.locked = (cache.get(key) or 0) >= LOGIN_FAILURE_LIMIT
        if self.locked:
            form = self.get_form()
            form.is_valid()
            return self.render_to_response(self.get_context_data(form=form), status=429)
        response = super().post(request, *args, **kwargs)
        if request.user.is_authenticated:
            cache.delete(key)
        else:
            _count_failure(key)
        return response


class LogoutView(auth_views.LogoutView):
    next_page = "/"
