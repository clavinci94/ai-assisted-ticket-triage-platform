"""Unit tests for the keyed TTL cache used by /tickets and /tickets/workbench."""

import time

from app.application.use_cases.read_cache import (
    KeyedTTLCache,
    invalidate_ticket_reads,
    tickets_list_cache,
    workbench_cache,
)


def test_different_keys_compute_independently():
    cache = KeyedTTLCache(ttl_seconds=60)
    calls = {}

    def compute_for(k):
        def _c():
            calls[k] = calls.get(k, 0) + 1
            return f"value-{k}"

        return _c

    cache.get_or_compute("a", compute_for("a"))
    cache.get_or_compute("b", compute_for("b"))
    cache.get_or_compute("a", compute_for("a"))  # hit
    assert calls == {"a": 1, "b": 1}


def test_ttl_expiry_recomputes():
    cache = KeyedTTLCache(ttl_seconds=0.05)
    calls = []
    cache.get_or_compute("k", lambda: calls.append(1) or "v1")
    time.sleep(0.1)
    cache.get_or_compute("k", lambda: calls.append(2) or "v2")
    assert calls == [1, 2]


def test_invalidate_drops_everything():
    cache = KeyedTTLCache(ttl_seconds=60)
    cache.get_or_compute("a", lambda: "v")
    cache.get_or_compute("b", lambda: "v")
    cache.invalidate()
    seen = []
    cache.get_or_compute("a", lambda: seen.append(1) or "v")
    assert seen == [1]


def test_invalidate_ticket_reads_clears_both_singletons():
    tickets_list_cache.get_or_compute("all", lambda: "x")
    workbench_cache.get_or_compute((1, 2), lambda: "y")
    invalidate_ticket_reads()

    seen = []
    tickets_list_cache.get_or_compute("all", lambda: seen.append("a") or "x")
    workbench_cache.get_or_compute((1, 2), lambda: seen.append("b") or "y")
    assert seen == ["a", "b"]
