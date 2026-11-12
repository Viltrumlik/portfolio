"""Studio forms. Every widget gets Atlas classes via style(); secrets use password inputs that never echo."""
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django import forms
from django.utils.text import slugify

from automations.models import Rule, ScheduledPost
from content.models import Experience, Post, Profile, Project, Service, Skill, SocialLink, Tag
from integrations.crypto import mask
from integrations.models import OutboundHook

from .catalog import EVENT_TYPES

CHECKBOXES = (forms.CheckboxInput, forms.CheckboxSelectMultiple)


def style(form):
    """Give text inputs, selects and textareas `at-field__input`, and checkboxes `st-check__input`."""
    for field in form.fields.values():
        widget = field.widget
        css = "st-check__input" if isinstance(widget, CHECKBOXES) else "at-field__input"
        widget.attrs["class"] = css
    return form


class AtlasForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style(self)


class AtlasModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style(self)


MAX_IMAGE_BYTES = 5 * 1024 * 1024


def limit_image_size(upload):
    """Uploaded pictures are capped at 5 MB; ImageField itself rejects files that aren't images."""
    if upload and getattr(upload, "size", 0) > MAX_IMAGE_BYTES:
        raise forms.ValidationError("That picture is over 5 MB. Export it smaller (1200×630 is plenty) and upload it again.")
    return upload


def secret_input():
    return forms.PasswordInput(render_value=False, attrs={"autocomplete": "new-password", "spellcheck": "false"})


# --- connections ----------------------------------------------------------------------
# Every field is optional here: integrations.actions validates and answers with a sentence the form shows.


class GitHubForm(AtlasForm):
    token = forms.CharField(label="Token", required=False, max_length=500, widget=secret_input())
    webhook_secret = forms.CharField(label="Webhook secret", required=False, max_length=500, widget=secret_input(),
                                     help_text="Used to verify X-Hub-Signature-256 on every delivery.")


class TelegramForm(AtlasForm):
    bot_token = forms.CharField(label="Bot token", required=False, max_length=200, widget=secret_input())
    channel_id = forms.CharField(label="Channel", required=False, max_length=200,
                                 help_text="Optional: @channel or a t.me link. Add the bot to the channel as an admin.")


class LastfmForm(AtlasForm):
    username = forms.CharField(label="Username", required=False, max_length=100)
    api_key = forms.CharField(label="API key", required=False, max_length=200, widget=secret_input())


CONNECT_FORMS = {"github": GitHubForm, "telegram": TelegramForm, "lastfm": LastfmForm}


# --- outgoing webhooks ----------------------------------------------------------------


class WebhookForm(AtlasModelForm):
    url = forms.URLField(label="URL", max_length=200, assume_scheme="https",
                         help_text="The https:// address of the n8n, Make or Zapier workflow.")
    secret = forms.CharField(label="Signing secret", required=False, max_length=200, widget=secret_input())
    events = forms.MultipleChoiceField(label="Events", required=False, choices=EVENT_TYPES, widget=forms.CheckboxSelectMultiple,
                                       help_text="Each event is sent as a signed POST. Rules can also send to this webhook.")
    field_order = ["name", "url", "secret", "events", "is_active"]

    class Meta:
        model = OutboundHook
        fields = ["name", "url", "is_active"]
        labels = {"name": "Name", "is_active": "Active"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        saved = mask((self.instance.secret or {}).get("secret", ""))
        self.fields["secret"].help_text = (
            f"Saved: {saved}. Leave empty to keep it, or type a new one to replace it." if saved
            else "Signs every delivery (X-Atlas-Signature, HMAC-SHA256). Use the same secret in the receiver."
        )
        if self.instance.pk:
            self.initial.setdefault("events", list(self.instance.events or []))

    def clean_url(self):
        url = self.cleaned_data["url"]
        if not url.lower().startswith("https://"):
            raise forms.ValidationError("Use an https:// URL.")
        return url

    def clean_secret(self):
        secret = self.cleaned_data["secret"].strip()
        if not secret and not (self.instance.secret or {}).get("secret"):
            raise forms.ValidationError("Add a signing secret so the receiver can check each delivery.")
        return secret

    def save(self, commit=True):
        hook = super().save(commit=False)
        hook.events = list(self.cleaned_data["events"])
        if self.cleaned_data["secret"]:
            hook.secret = {"secret": self.cleaned_data["secret"]}
        if commit:
            hook.save()
        return hook


# --- automation rules -----------------------------------------------------------------


class RuleForm(AtlasForm):
    name = forms.CharField(label="Name", max_length=120)
    trigger = forms.ChoiceField(label="When", choices=EVENT_TYPES)
    repo = forms.CharField(label="Repos", required=False, max_length=500,
                           help_text="Optional, comma-separated (volunteers_bot, pul-olami). Empty means any repo.")
    branch = forms.CharField(label="Branch", required=False, max_length=200, help_text="Optional, for pushes (main).")
    action = forms.ChoiceField(label="Then", choices=Rule.Action.choices)
    template = forms.CharField(label="Message", required=False, max_length=4000, widget=forms.Textarea(attrs={"rows": 5, "data-template-input": True}),
                               help_text="{{key}} inserts a value from the event, such as {{repo}}.")
    hook = forms.ModelChoiceField(label="Webhook", required=False, queryset=OutboundHook.objects.order_by("name"),
                                  empty_label="Pick a webhook", help_text="Used by “Send to a webhook”.")

    def __init__(self, *args, rule=None, **kwargs):
        self.rule = rule or Rule(is_enabled=False)
        if rule is not None:
            filters, config = rule.filters or {}, rule.action_config or {}
            repos = filters.get("repo") or []
            kwargs.setdefault("initial", {
                "name": rule.name, "trigger": rule.trigger, "action": rule.action,
                "repo": ", ".join(repos if isinstance(repos, list) else [repos]),
                "branch": filters.get("branch", ""), "template": config.get("template", ""), "hook": config.get("hook_id"),
            })
        super().__init__(*args, **kwargs)
        if self.rule.is_builtin:  # built-in rules are matched by trigger + action; keep them fixed
            for name in ("trigger", "action"):
                self.fields[name].disabled = True
                self.fields[name].help_text = "Fixed for built-in rules."

    def clean(self):
        data = super().clean()
        action = data.get("action")
        if action == Rule.Action.WEBHOOK_SEND and not data.get("hook"):
            self.add_error("hook", "Pick a webhook for this rule.")
        if action in (Rule.Action.TELEGRAM_SEND, Rule.Action.TELEGRAM_POST) and not (data.get("template") or "").strip():
            self.add_error("template", "Write the message to send.")
        return data

    def save(self):
        data, rule = self.cleaned_data, self.rule
        filters = {}
        repos = [r.strip() for r in data["repo"].split(",") if r.strip()]
        if repos:
            filters["repo"] = repos
        if data["branch"].strip():
            filters["branch"] = data["branch"].strip()
        if data["action"] in (Rule.Action.TELEGRAM_SEND, Rule.Action.TELEGRAM_POST):
            config = {"template": data["template"].strip()}
        elif data["action"] == Rule.Action.WEBHOOK_SEND:
            config = {"hook_id": data["hook"].pk}
        else:
            config = {}
        rule.name, rule.trigger, rule.action = data["name"], data["trigger"], data["action"]
        rule.filters, rule.action_config = filters, config
        rule.save()
        return rule


# --- content --------------------------------------------------------------------------


def _date_input():
    return forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")


def _split_list(text):
    return [part.strip() for part in (text or "").split(",") if part.strip()]


class ProfileForm(AtlasModelForm):
    class Meta:
        model = Profile
        fields = ["name", "handle", "headline", "bio", "location", "timezone", "email", "availability", "availability_note"]
        labels = {"availability_note": "Availability note", "bio": "Bio", "timezone": "Time zone"}
        help_texts = {
            "headline": "One sentence, first person: what you build and for whom.",
            "bio": "Markdown.",
            "timezone": "An IANA name, such as Asia/Tashkent. Times on the site use it.",
            "availability_note": "Shown instead of the status, e.g. “Booked until March”.",
        }
        widgets = {"bio": forms.Textarea(attrs={"rows": 8})}

    def clean_timezone(self):
        name = self.cleaned_data["timezone"].strip()
        try:
            ZoneInfo(name)
        except (ZoneInfoNotFoundError, ValueError):
            raise forms.ValidationError("Use a time zone name such as Asia/Tashkent.")
        return name


class ExperienceForm(AtlasModelForm):
    class Meta:
        model = Experience
        fields = ["role", "company", "location", "start_date", "end_date", "description", "order"]
        help_texts = {"end_date": "Leave empty while it is current.", "description": "Markdown."}
        widgets = {"start_date": _date_input(), "end_date": _date_input(), "description": forms.Textarea(attrs={"rows": 5})}

    def clean(self):
        data = super().clean()
        start, end = data.get("start_date"), data.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "The end date is before the start date.")
        return data


class SkillForm(AtlasModelForm):
    class Meta:
        model = Skill
        fields = ["name", "group", "order"]
        help_texts = {"group": "Skills with the same group are listed together (Backend, Bots…)."}


class ServiceForm(AtlasModelForm):
    class Meta:
        model = Service
        fields = ["title", "description", "order"]
        help_texts = {"description": "Markdown."}
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}


class SocialLinkForm(AtlasModelForm):
    url = forms.URLField(label="URL", max_length=200, assume_scheme="https")
    field_order = ["platform", "label", "url", "order"]

    class Meta:
        model = SocialLink
        fields = ["platform", "label", "url", "order"]
        help_texts = {"platform": "github, telegram, linkedin, email…", "label": "Optional; defaults to the platform."}


class PostForm(AtlasModelForm):
    tags = forms.CharField(label="Tags", required=False, max_length=500, help_text="Comma-separated: Django, Bots.")
    field_order = ["title", "slug", "excerpt", "cover", "body", "tags", "status"]

    class Meta:
        model = Post
        fields = ["title", "slug", "excerpt", "cover", "body", "status"]
        help_texts = {"slug": "Leave empty to make one from the title.", "body": "Markdown.", "excerpt": "One or two sentences for lists and previews."}
        widgets = {"excerpt": forms.Textarea(attrs={"rows": 3}), "body": forms.Textarea(attrs={"rows": 18, "spellcheck": "true"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        if self.instance.pk:
            self.initial["tags"] = ", ".join(t.name for t in self.instance.tags.all())

    def clean_slug(self):
        slug = self.cleaned_data.get("slug") or ""
        if slug:
            return slug
        base = slugify(self.cleaned_data.get("title") or "")[:200] or "post"
        slug, n = base, 2
        while Post.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
            slug, n = f"{base}-{n}", n + 1
        return slug

    def clean_cover(self):
        return limit_image_size(self.cleaned_data.get("cover"))

    def save_tags(self, post):
        tags = []
        for name in _split_list(self.cleaned_data.get("tags")):
            slug = slugify(name)[:70]
            if slug:
                tag, _ = Tag.objects.get_or_create(slug=slug, defaults={"name": name[:60]})
                tags.append(tag)
        post.tags.set(tags)


class ProjectForm(AtlasModelForm):
    stack = forms.CharField(label="Stack", required=False, max_length=500, help_text="Comma-separated: Python, aiogram, PostgreSQL.")

    class Meta:
        model = Project
        fields = ["title", "summary", "kind", "stack", "image", "case_study", "featured", "hidden", "order"]
        labels = {"case_study": "Case study", "featured": "Featured on the home page", "hidden": "Hidden from the site",
                  "image": "Screenshot"}
        help_texts = {"title": "Leave empty to use the repo name.", "case_study": "Markdown."}
        widgets = {"summary": forms.Textarea(attrs={"rows": 3}), "case_study": forms.Textarea(attrs={"rows": 14})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial["stack"] = ", ".join(str(s) for s in (self.instance.stack or []))

    def clean_stack(self):
        return _split_list(self.cleaned_data.get("stack"))

    def clean_image(self):
        return limit_image_size(self.cleaned_data.get("image"))


class ScheduledPostForm(AtlasModelForm):
    """A channel post. publish_at is read and shown in the time zone active in the view (the owner's)."""

    image_url = forms.URLField(label="Picture URL", required=False, assume_scheme="https",
                               help_text="A public picture URL. Overrides the project's picture.")

    class Meta:
        model = ScheduledPost
        fields = ["text", "project", "image_url", "publish_at"]
        labels = {"image_url": "Picture URL", "publish_at": "Publish at"}
        widgets = {
            "text": forms.Textarea(attrs={"rows": 18, "spellcheck": "true"}),
            "publish_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, tz_label="", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["publish_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        if tz_label:
            self.fields["publish_at"].help_text = f"Your local time ({tz_label})."
        self.fields["project"].queryset = Project.objects.order_by("hidden", "order", "slug")
        self.fields["project"].empty_label = "No project (text only)"

    def clean(self):
        data = super().clean()
        text = data.get("text") or ""
        project = data.get("project")
        has_picture = bool(data.get("image_url") or (project and not project.hidden))
        limit = 1024 if has_picture else 4096
        if len(text) > limit:
            where = "a photo caption" if has_picture else "a post"
            self.add_error("text", f"Telegram allows {limit} characters in {where}; this has {len(text)}.")
        return data
