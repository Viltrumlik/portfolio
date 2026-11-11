from django.apps import AppConfig


class AutomationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "automations"

    def ready(self):
        from . import engine  # noqa: F401  (registers the automations.dispatch job handler)
