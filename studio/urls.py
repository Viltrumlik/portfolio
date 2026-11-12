"""The owner's studio. Every route except login/logout is wrapped in staff_required here, so none can slip through."""
from django.urls import path

from .auth import LoginView, LogoutView, staff_required
from .views import automations, channel, connections, content, desk, inbox, jobs, webhooks

app_name = "studio"


def staff(route, view, name):
    return path(route, staff_required(view), name=name)


urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    staff("", desk.desk, "desk"),
    # connections
    staff("connections/telegram/verify/", connections.verify_telegram, "telegram_verify"),
    staff("connections/<str:provider>/", connections.connection, "connection"),
    staff("connections/<str:provider>/disconnect/", connections.disconnect, "disconnect"),
    staff("connections/<str:provider>/sync/", connections.sync_now, "sync"),
    # outgoing webhooks
    staff("webhooks/", webhooks.webhook_list, "webhooks"),
    staff("webhooks/<int:pk>/", webhooks.webhook_edit, "webhook"),
    staff("webhooks/<int:pk>/test/", webhooks.webhook_test, "webhook_test"),
    staff("webhooks/<int:pk>/delete/", webhooks.webhook_delete, "webhook_delete"),
    # automation rules
    staff("channel/", channel.post_list, "channel"),
    staff("channel/new/", channel.post_edit, "channel_new"),
    staff("channel/<int:pk>/", channel.post_edit, "channel_post"),
    staff("channel/<int:pk>/cancel/", channel.cancel, "channel_cancel"),
    staff("automations/", automations.rule_list, "automations"),
    staff("automations/new/", automations.rule_edit, "rule_new"),
    staff("automations/<int:pk>/", automations.rule_edit, "rule"),
    staff("automations/<int:pk>/toggle/", automations.rule_toggle, "rule_toggle"),
    staff("automations/<int:pk>/delete/", automations.rule_delete, "rule_delete"),
    # content
    staff("content/", content.index, "content"),
    staff("content/posts/", content.post_list, "posts"),
    staff("content/posts/new/", content.post_edit, "post_new"),
    staff("content/posts/<int:pk>/", content.post_edit, "post"),
    staff("content/projects/", content.project_list, "projects"),
    staff("content/projects/<int:pk>/", content.project_edit, "project"),
    staff("content/<slug:kind>/", content.item_list, "items"),
    staff("content/<slug:kind>/new/", content.item_edit, "item_new"),
    staff("content/<slug:kind>/<int:pk>/", content.item_edit, "item"),
    staff("content/<slug:kind>/<int:pk>/delete/", content.item_delete, "item_delete"),
    # inbox and jobs
    staff("inbox/", inbox.inbox, "inbox"),
    staff("inbox/<int:pk>/read/", inbox.mark_read, "inbox_read"),
    staff("inbox/<int:pk>/delete/", inbox.delete, "inbox_delete"),
    staff("jobs/", jobs.failed_jobs, "jobs"),
    staff("jobs/<int:pk>/retry/", jobs.retry, "job_retry"),
]
