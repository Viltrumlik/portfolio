import pytest
from cryptography.fernet import Fernet
from django.db import connection as db
from django.test import override_settings

from integrations.crypto import decrypt_json, encrypt_json
from integrations.models import Connection

pytestmark = pytest.mark.django_db


def test_credentials_round_trip_through_the_database():
    Connection.objects.create(provider="github", credentials={"token": "ghp_secret123"})
    assert Connection.objects.get(provider="github").credentials == {"token": "ghp_secret123"}


def test_credentials_are_not_stored_in_plaintext():
    Connection.objects.create(provider="github", credentials={"token": "ghp_secret123"})
    with db.cursor() as cur:
        cur.execute("SELECT credentials FROM integrations_connection")
        raw = cur.fetchone()[0]
    assert "ghp_secret123" not in raw


def test_old_key_still_decrypts_after_rotation():
    old, new = Fernet.generate_key().decode(), Fernet.generate_key().decode()
    with override_settings(ATLAS_FERNET_KEYS=[old]):
        token = encrypt_json({"api_key": "k1"})
    with override_settings(ATLAS_FERNET_KEYS=[new, old]):
        assert decrypt_json(token) == {"api_key": "k1"}
