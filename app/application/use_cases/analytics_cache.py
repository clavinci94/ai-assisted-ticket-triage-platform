"""Tiny TTL cache for the dashboard analytics result.

The analytics computation reads every ticket from the DB and runs ~20
aggregations over them. Each ReportsPage / dashboard load fires the
``/tickets/analytics`` endpoint, so without caching every page refresh
triggers the same full-table scan.

This is a process-local cache: simple to reason about, no Redis
dependency, fine for a single-worker FastAPI process on Render Free. If
the deploy ever scales horizontally, swap this for a real shared cache.

API:

    cache = AnalyticsCache(ttl_seconds=60)
    cache.get_or_compute(lambda: expensive_computation())
    cache.invalidate()  # called from /tickets/decision and admin routes
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from time import monotonic
from typing import Any

logger = logging.getLogger(__name__)


class AnalyticsCache:
    def __init__(self, ttl_seconds: float = 60.0) -> None:
        self._ttl = float(ttl_seconds)
        self._lock = threading.Lock()
        self._value: Any = None
        self._expires_at: float = 0.0

    def get_or_compute(self, compute: Callable[[], Any]) -> Any:
        now = monotonic()
        # Lock-free fast path: read the snapshot without contention.
        value = self._value
        if value is not None and now < self._expires_at:
            return value

        # Cache miss / stale: serialise computation so concurrent loaders
        # don't all do the same expensive aggregation.
        with self._lock:
            now = monotonic()
            if self._value is not None and now < self._expires_at:
                return self._value
            self._value = compute()
            self._expires_at = now + self._ttl
            return self._value

    def invalidate(self) -> None:
        with self._lock:
            self._value = None
            self._expires_at = 0.0


# Process-wide singleton. Imported by both the analytics route (read path)
# and any write path that should invalidate (e.g. /tickets/decision).
analytics_cache = AnalyticsCache(ttl_seconds=60.0)
