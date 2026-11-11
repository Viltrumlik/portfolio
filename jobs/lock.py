"""One job runner at a time: a non-blocking fcntl lock on settings.JOBS_LOCK_FILE."""
import fcntl
from contextlib import contextmanager
from pathlib import Path

from django.conf import settings


@contextmanager
def job_lock(path=None):
    """Yield True while holding the lock, or False at once if another process holds it."""
    path = Path(path or settings.JOBS_LOCK_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
