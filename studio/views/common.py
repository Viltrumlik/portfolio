"""Small helpers shared by the studio views."""
from django.utils.http import url_has_allowed_host_and_scheme


def safe_next(request, default):
    """The POSTed `next` if it is a local path, else `default`."""
    target = request.POST.get("next") or ""
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return target
    return default
