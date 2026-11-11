"""The studio desk: one window per connection, the sync log, and a dock of connected services."""
from django.shortcuts import render
from django.views.decorators.http import require_GET

from integrations.models import OutboundHook

from ..presenters import dock_items, integration_cards, sync_log

# Connection windows sit on a two-column grid; the sync log is the tall window on the right.
SLOTS = [("2%", 24), ("35%", 24), ("2%", 480), ("35%", 480)]


@require_GET
def desk(request):
    cards = integration_cards()
    for i, card in enumerate(cards):
        card["x"], card["y"] = SLOTS[i % len(SLOTS)]
        card["delay"] = i * 100
    hooks = OutboundHook.objects.order_by("name")
    hooks_x, hooks_y = SLOTS[len(cards) % len(SLOTS)]
    return render(request, "studio/desk.html", {
        "cards": cards,
        "log": sync_log(),
        "dock_items": dock_items(cards),
        "hooks": hooks,
        "hooks_pos": {"x": hooks_x, "y": hooks_y, "delay": len(cards) * 100},
    })
