"""Redis caching helpers (Flask-Caching with RedisCache backend).

We use *namespace version keys* for invalidation: every cached value key
contains the current version of its namespace (e.g. ``exams:v7:list``).
Bumping the version after a write makes every old key unreachable and they
expire on their own (TTL) – cheap and safe invalidation.
"""
from flask import g, current_app
from flask_caching import Cache

cache = Cache()

# Default TTLs (seconds) – cache expiry
TTL_EXAMS = 300        # frequently accessed examinations
TTL_SCHEDULE = 60      # slot schedules change more often
TTL_RUBRICS = 600      # rubrics rarely change
TTL_STATS = 30


def _ver(ns):
    try:
        return cache.get(f"ver:{ns}") or 1
    except Exception:  # Redis down -> behave like no cache
        return 1


def cached(ns, key, ttl, producer):
    """Return cached value for (namespace, key) or compute + store it."""
    full_key = f"{ns}:v{_ver(ns)}:{key}"
    try:
        value = cache.get(full_key)
    except Exception:
        value = None
    if value is not None:
        g.cache_status = "HIT"
        return value
    g.cache_status = "MISS"
    value = producer()
    try:
        cache.set(full_key, value, timeout=ttl)
    except Exception:
        current_app.logger.warning("Redis cache unavailable – serving uncached data")
    return value


def invalidate(*namespaces):
    """Bump version of namespaces so previous cached values are ignored."""
    for ns in namespaces:
        try:
            v = cache.get(f"ver:{ns}") or 1
            cache.set(f"ver:{ns}", v + 1, timeout=0)
        except Exception:
            pass


def invalidate_exam_data():
    invalidate("exams", "schedule", "rubrics", "stats")
