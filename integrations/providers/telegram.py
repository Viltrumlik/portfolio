"""Telegram Bot API: verify a bot, find the owner's chat, send messages and channel posts."""
import html
import re

from .. import http
from ..errors import AuthError, Permanent, RateLimited, Transient

SERVICE = "Telegram"
MAX_TEXT = 4096


def escape_html(value):
    """Escape a value for Telegram's HTML parse mode (&, <, >)."""
    return html.escape("" if value is None else str(value), quote=False)


_ALLOWED_TAG = re.compile(
    r"&lt;(/?)(b|strong|i|em|u|ins|s|strike|del|code|pre|blockquote|tg-spoiler)&gt;"
    r'|&lt;a href="([^"<>&]*)"&gt;|&lt;/a&gt;'
)


def template_markup(template):
    """Escape a rule template's own text for HTML mode, keeping the tags Telegram supports.

    "New message from {{name}} <{{email}}>" must not reach Telegram as an unknown <...> tag,
    while "<b>New release</b>" stays bold. Placeholders are left for render_template.
    """

    def restore(match):
        if match.group(2):
            return f"<{match.group(1)}{match.group(2)}>"
        if match.group(3) is not None:
            return f'<a href="{match.group(3)}">'
        return "</a>"

    return _ALLOWED_TAG.sub(restore, escape_html(template or ""))


def _call(bot_token, method, *, forbidden="", http_method="POST", **params):
    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    if http_method == "GET":
        response = http.request("GET", url, service=SERVICE, params=params or None)
    else:
        response = http.request("POST", url, service=SERVICE, json=params)
    try:
        body = response.json()
    except ValueError:
        body = {}
    status = response.status_code
    if status == 200 and body.get("ok"):
        return body.get("result")
    description = str(body.get("description") or f"HTTP {status}").replace(bot_token, "•••")
    if status == 401:
        raise AuthError("Telegram rejected the bot token. Paste a new token from @BotFather.", code="401")
    if status == 403:
        raise Permanent(forbidden or f"Telegram refused: {description}.", code="403")
    if status == 429:
        retry_after = (body.get("parameters") or {}).get("retry_after") or 30
        raise RateLimited(retry_after, f"Telegram asked us to wait {retry_after}s.", code="429")
    if status >= 500:
        raise Transient(f"Telegram is having trouble ({status}). It will retry.", code=str(status))
    raise Permanent(f"Telegram refused the request: {description}.", code=str(status))


def verify(bot_token):
    """getMe -> {"id", "username"}."""
    me = _call(bot_token, "getMe", http_method="GET")
    return {"id": me["id"], "username": me.get("username", "")}


def find_chat_id(bot_token):
    """The chat id of the latest private chat that sent /start to the bot, or None."""
    updates = _call(bot_token, "getUpdates", http_method="GET") or []
    for update in reversed(updates):
        message = update.get("message") or {}
        chat = message.get("chat") or {}
        text = (message.get("text") or "").strip()
        if chat.get("type") == "private" and (text == "/start" or text.startswith("/start ")):
            return chat["id"]
    return None


def _fit(text):
    """Cut to Telegram's limit without leaving half an HTML entity at the end."""
    if len(text) <= MAX_TEXT:
        return text
    cut = re.sub(r"&[#a-zA-Z0-9]*$", "", text[: MAX_TEXT - 1])
    return cut + "…"


def send_message(connection, text, chat_id=None):
    """Send `text` (HTML; escape interpolated values with escape_html) to the owner's chat."""
    chat_id = chat_id or (connection.config or {}).get("chat_id")
    if not chat_id:
        raise Permanent("Telegram has no chat to write to. Send /start to the bot, then verify the chat.", code="no_chat")
    return _call(
        connection.credentials["bot_token"],
        "sendMessage",
        forbidden="Telegram refused: the bot was blocked by the user. Unblock it and send /start again.",
        chat_id=chat_id,
        text=_fit(text),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


def post_channel(connection, text):
    """Post `text` (HTML) to config["channel_id"]."""
    channel_id = (connection.config or {}).get("channel_id")
    if not channel_id:
        raise Permanent("No Telegram channel is set. Add the channel id on the Telegram connection.", code="no_channel")
    return _call(
        connection.credentials["bot_token"],
        "sendMessage",
        forbidden="Telegram refused: the bot is not an admin of the channel. Add it as an admin who can post messages.",
        chat_id=channel_id,
        text=_fit(text),
        parse_mode="HTML",
    )
