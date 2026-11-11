"""Job handlers and periodic schedulers.

    @handler("github.sync")
    def github_sync(payload): ...

    @periodic
    def schedule_polls(now): ...   # called by `manage.py run_jobs` before running due jobs

Apps register theirs by importing their handler modules in AppConfig.ready().
"""

_handlers = {}
_periodic = []


def handler(kind):
    def register(fn):
        _handlers[kind] = fn
        return fn

    return register


def get(kind):
    """The handler for `kind`, or None."""
    return _handlers.get(kind)


def kinds():
    return sorted(_handlers)


def periodic(fn):
    if fn not in _periodic:
        _periodic.append(fn)
    return fn


def periodic_tasks():
    return list(_periodic)
