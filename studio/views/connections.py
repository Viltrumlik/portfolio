"""Connect, replace, disconnect and sync services. All side effects go through integrations.actions."""
from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from integrations import actions
from integrations.errors import IntegrationError
from integrations.models import Connection
from integrations.services import connection_summary

from ..catalog import PROVIDERS
from ..forms import CONNECT_FORMS
from ..presenters import integration_card
from .common import safe_next

SECRET_FIELDS = {"github": "token", "telegram": "bot_token", "lastfm": "api_key"}
SECRET_HINTS = {
    "github": "A classic or fine-grained token with read access to your repos.",
    "telegram": "From @BotFather in Telegram.",
    "lastfm": "From last.fm/api/account/create.",
}


def _provider(provider):
    if provider not in PROVIDERS:
        raise Http404("Unknown service")
    return provider


def _initial(provider, conn):
    config = (conn.config if conn else {}) or {}
    if provider == "telegram":
        return {"channel_id": config.get("channel_id", "")}
    if provider == "lastfm":
        return {"username": config.get("username") or (conn.account if conn else "")}
    return {}


def _connect(provider, data, conn):
    """Run the provider's connect action. An empty secret field keeps the saved secret."""
    saved = (conn.credentials if conn else {}) or {}
    secret = data[SECRET_FIELDS[provider]] or saved.get(SECRET_FIELDS[provider], "")
    if provider == "github":
        return actions.connect_github(secret, data["webhook_secret"])
    if provider == "telegram":
        return actions.connect_telegram(secret, data["channel_id"])
    return actions.connect_lastfm(data["username"], secret)


def _connected_message(provider, conn):
    name = PROVIDERS[provider]["name"]
    text = f"{name} connected as {conn.account}."
    if provider == "telegram" and not (conn.config or {}).get("chat_id"):
        return text + f" Send /start to {conn.account}, then verify the chat."
    return text + " The first sync is queued."


@require_http_methods(["GET", "POST"])
def connection(request, provider):
    provider = _provider(provider)
    conn = Connection.objects.filter(provider=provider).first()
    form_class = CONNECT_FORMS[provider]
    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            try:
                conn = _connect(provider, form.cleaned_data, conn)
            except IntegrationError as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(request, _connected_message(provider, conn))
                return redirect("studio:connection", provider)
    else:
        form = form_class(initial=_initial(provider, conn))

    card = integration_card(connection_summary()[provider])
    secret = form[SECRET_FIELDS[provider]]
    label = PROVIDERS[provider]["secret_label"].lower()
    if card["secret"]:
        secret.help_text = f"Saved: {card['secret']}. Leave empty to keep it, or paste a new {label} to replace it."
    else:
        secret.help_text = SECRET_HINTS[provider]
    if provider == "github" and card.get("webhook_secret_set"):
        form["webhook_secret"].help_text = "A secret is saved. Leave empty to keep it. Used to verify X-Hub-Signature-256 on every delivery."
    return render(request, "studio/connection.html", {
        "provider": provider,
        "card": card,
        "form": form,
        "submit_label": f"Connect {card['name']}" if card["status"] == "off" else f"Reconnect {card['name']}",
        "webhook_url": settings.SITE_URL.rstrip("/") + reverse("integrations:github-webhook"),
    })


@require_http_methods(["GET", "POST"])
def disconnect(request, provider):
    """GET asks once, in a sentence; POST disconnects."""
    provider = _provider(provider)
    name = PROVIDERS[provider]["name"]
    if request.method == "POST":
        actions.disconnect(provider)
        messages.success(request, f"{name} disconnected. Cached data stays on the site.")
        return redirect("studio:desk")
    return render(request, "studio/disconnect.html", {
        "provider": provider,
        "name": name,
        "question": PROVIDERS[provider]["disconnect"],
    })


@require_POST
def sync_now(request, provider):
    provider = _provider(provider)
    try:
        actions.request_sync(provider)
    except IntegrationError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"{PROVIDERS[provider]['name']} sync queued. It starts within a minute.")
    return redirect(safe_next(request, reverse("studio:connection", args=[provider])))


@require_POST
def verify_telegram(request):
    try:
        conn = actions.verify_telegram_chat()
    except IntegrationError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"Chat verified. {conn.account or 'The bot'} sent you a confirmation.")
    return redirect("studio:connection", "telegram")
