"""Unit tests for the analytics TTL cache."""

import time

from app.application.use_cases.analytics_cache import AnalyticsCache


def test_first_call_computes():
    cache = AnalyticsCache(ttl_seconds=60)
    calls = []
    result = cache.get_or_compute(lambda: calls.append(1) or "value")
    assert result == "value"
    assert len(calls) == 1


def test_second_call_within_ttl_is_cached():
    cache = AnalyticsCache(ttl_seconds=60)
    calls = []

    def compute():
        calls.append(1)
        return "value"

    cache.get_or_compute(compute)
    cache.get_or_compute(compute)
    cache.get_or_compute(compute)
    assert len(calls) == 1


def test_call_after_ttl_recomputes():
    cache = AnalyticsCache(ttl_seconds=0.05)
    calls = []
    cache.get_or_compute(lambda: calls.append(1) or "v1")
    time.sleep(0.1)
    cache.get_or_compute(lambda: calls.append(2) or "v2")
    assert calls == [1, 2]


def test_invalidate_forces_recompute():
    cache = AnalyticsCache(ttl_seconds=60)
    calls = []

    def compute():
        calls.append(len(calls))
        return f"v{len(calls)}"

    cache.get_or_compute(compute)
    cache.invalidate()
    cache.get_or_compute(compute)
    assert len(calls) == 2
