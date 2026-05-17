"""Keyed TTL cache for read endpoints.

The existing AnalyticsCache caches a single value (the analytics
aggregate). For list / paginated endpoints we need a per-query-params
cache so e.g. ``/tickets/workbench?page=1`` and
``?page=2&sort_by=composite_priority`` don't share the same slot.

Process-local, thread-safe, no eviction by count — fine for the demo
(single user, <20 distinct param combos). Swap for cachetools or Redis
if the deploy ever scales horizontally.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Hashable
from time import monotonic
from typing import Any


class KeyedTTLCache:
    def __init__(self, ttl_seconds: float = 30.0) -> None:
        self._ttl = float(ttl_seconds)
        self._lock = threading.Lock()
        self._entries: dict[Hashable, tuple[float, Any]] = {}

    def get_or_compute(self, key: Hashable, compute: Callable[[], Any]) -> Any:
        now = monotonic()
        entry = self._entries.get(key)
        if entry is not None:
            expires_at, value = entry
            if now < expires_at:
                return value

        with self._lock:
            now = monotonic()
            entry = self._entries.get(key)
            if entry is not None:
                expires_at, value = entry
                if now < expires_at:
                    return value
            value = compute()
            self._entries[key] = (now + self._ttl, value)
            return value

    def invalidate(self) -> None:
        with self._lock:
            self._entries.clear()


# Process-wide singletons. Imported by the read routes (read path) and
# the mutation routes (invalidate after writes).
tickets_list_cache = KeyedTTLCache(ttl_seconds=30.0)
workbench_cache = KeyedTTLCache(ttl_seconds=15.0)


def invalidate_ticket_reads() -> None:
    """Drop every cached ticket read. Called from mutation handlers."""

    tickets_list_cache.invalidate()
    workbench_cache.invalidate()
