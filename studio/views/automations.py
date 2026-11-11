"""Automation rules: one trigger, one action. New rules start off; built-in rules can't be deleted."""
import json

from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from automations.engine import render_template
from automations.models import Rule
from integrations.models import Connection, OutboundHook

from ..catalog import EVENT_TYPES, SAMPLES
from ..forms import RuleForm
from ..presenters import rule_card, rule_runs
from .common import safe_next


def _context_for_cards():
    hooks = {h.pk: h for h in OutboundHook.objects.all()}
    telegram = Connection.objects.filter(provider="telegram").exclude(status=Connection.Status.OFF).first()
    return hooks, telegram


@require_GET
def rule_list(request):
    hooks, telegram = _context_for_cards()
    cards = [rule_card(rule, hooks, telegram) for rule in Rule.objects.order_by("-is_enabled", "name", "pk")]
    return render(request, "studio/automations.html", {"cards": cards, "hook_count": len(hooks)})


@require_http_methods(["GET", "POST"])
def rule_edit(request, pk=None):
    rule = get_object_or_404(Rule, pk=pk) if pk else None
    form = RuleForm(request.POST or None, rule=rule)
    if request.method == "POST" and form.is_valid():
        saved = form.save()
        if rule is None:
            messages.success(request, f"Rule “{saved.name}” created. It stays off until you turn it on.")
        else:
            messages.success(request, f"Rule “{saved.name}” saved.")
        return redirect("studio:rule", saved.pk)

    trigger = form["trigger"].value() or (rule.trigger if rule else EVENT_TYPES[0][0])
    sample = SAMPLES.get(trigger, {})
    hooks, telegram = _context_for_cards()
    return render(request, "studio/rule_edit.html", {
        "rule": rule,
        "form": form,
        "card": rule_card(rule, hooks, telegram) if rule else None,
        "runs": rule_runs(rule) if rule else [],
        "sample_json": json.dumps(sample, ensure_ascii=False),
        "preview": render_template(form["template"].value() or "", sample),
        "sample_keys": list(sample),
    })


@require_POST
def rule_toggle(request, pk):
    rule = get_object_or_404(Rule, pk=pk)
    wanted = request.POST.get("enabled")
    rule.is_enabled = (wanted == "1") if wanted in ("0", "1") else not rule.is_enabled
    rule.save(update_fields=["is_enabled"])
    messages.success(request, f"“{rule.name}” is {'on' if rule.is_enabled else 'off'}.")
    return redirect(safe_next(request, reverse("studio:automations")))


@require_POST
def rule_delete(request, pk):
    rule = get_object_or_404(Rule, pk=pk)
    if rule.is_builtin:
        return HttpResponseForbidden("Built-in rules can’t be deleted. Turn the rule off instead.")
    rule.delete()
    messages.success(request, f"Rule “{rule.name}” deleted.")
    return redirect("studio:automations")
