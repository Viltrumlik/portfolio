from django.db import models

from .crypto import decrypt_json, encrypt_json


class EncryptedJSONField(models.TextField):
    """A JSON value stored Fernet-encrypted. Use for tokens, API keys and secrets."""

    def from_db_value(self, value, expression, connection):
        return decrypt_json(value) if value else {}

    def to_python(self, value):
        return value if not isinstance(value, str) else decrypt_json(value)

    def get_prep_value(self, value):
        return encrypt_json(value if value is not None else {})
