from django.conf import settings

CSP_EXEMPT_PREFIXES = ("/admin/",)  # the Unfold admin relies on Alpine.js, which a strict script-src breaks
PERMISSIONS_POLICY = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"


def content_security_policy():
    dev = (settings.VITE_DEV_SERVER or "").rstrip("/")
    script_src = "'self'" + (f" {dev}" if dev else "")
    connect_src = "'self'" + (f" {dev} ws:" if dev else "")
    return "; ".join([
        "default-src 'self'",
        "img-src 'self' data: https:",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src https://fonts.gstatic.com",
        f"script-src {script_src}",
        f"connect-src {connect_src}",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
    ])


class SecurityHeadersMiddleware:
    """Adds Content-Security-Policy and Permissions-Policy to every response (CSP skipped under /admin/)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not request.path.startswith(CSP_EXEMPT_PREFIXES) and "Content-Security-Policy" not in response:
            response["Content-Security-Policy"] = content_security_policy()
        if "Permissions-Policy" not in response:
            response["Permissions-Policy"] = PERMISSIONS_POLICY
        return response
