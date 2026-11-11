"""Encryption for secrets stored in the database (Fernet / MultiFernet)."""
import json

from cryptography.fernet import Fernet, MultiFernet
from django.conf import settings


def _fernet():
    return MultiFernet([Fernet(k.encode() if isinstance(k, str) else k) for k in settings.ATLAS_FERNET_KEYS])


def encrypt_json(value):
    return _fernet().encrypt(json.dumps(value, separators=(",", ":")).encode()).decode()


def decrypt_json(token):
    return json.loads(_fernet().decrypt(token.encode()).decode())


def mask(secret, keep=4):
    """'ghp_abcdef1234' -> '•••• 1234' (never show a full secret)."""
    secret = str(secret or "")
    return ("\u2022\u2022\u2022\u2022 " + secret[-keep:]) if secret else ""
