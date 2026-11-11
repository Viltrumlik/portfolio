from .models import Profile

THEMES = ("dark", "light")


def site(request):
    theme = request.COOKIES.get("theme", "dark")
    return {"profile": Profile.load(), "theme": theme if theme in THEMES else "dark"}
