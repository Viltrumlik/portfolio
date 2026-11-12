from .models import Profile

# Phosphor themes; the first is the default. Unknown and pre-Matrix values (dark/light) fall back to it.
THEMES = ("green", "amber", "ice")


def site(request):
    theme = request.COOKIES.get("theme", THEMES[0])
    return {"profile": Profile.load(), "theme": theme if theme in THEMES else THEMES[0]}
