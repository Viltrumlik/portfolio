import pytest

from integrations.tests.fixtures import api, no_network, resolve_to  # noqa: F401
from jobs import registry


@pytest.fixture
def handlers():
    """Register throwaway handlers for one test; the real registry is restored afterwards."""
    saved = dict(registry._handlers)
    yield registry
    registry._handlers.clear()
    registry._handlers.update(saved)
