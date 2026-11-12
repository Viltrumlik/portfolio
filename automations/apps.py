from django.apps import AppConfig


class AutomationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "automations"

    def ready(self):
        from . import channel, engine  # noqa: F401  (register job handlers and the channel queue)
