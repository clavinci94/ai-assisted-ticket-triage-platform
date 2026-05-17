import { afterEach, describe, expect, it, vi } from "vitest";

import { clear, invalidate, swr } from "./swrCache";

afterEach(() => {
  clear();
  vi.useRealTimers();
});

describe("swrCache", () => {
  it("computes on cold cache, returns cached on warm hit", async () => {
    const fetcher = vi.fn().mockResolvedValue("v1");

    expect(await swr("k", fetcher, { ttlMs: 60_000 })).toBe("v1");
    expect(await swr("k", fetcher, { ttlMs: 60_000 })).toBe("v1");
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("dedupes concurrent cold-cache fetches", async () => {
    const fetcher = vi.fn().mockResolvedValue("v");
    await Promise.all([swr("k", fetcher), swr("k", fetcher), swr("k", fetcher)]);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("returns stale value immediately and refreshes in background", async () => {
    let counter = 0;
    const fetcher = vi.fn(async () => {
      counter += 1;
      return `v${counter}`;
    });

    // Initial fill — TTL short enough that it expires while we wait.
    expect(await swr("k", fetcher, { ttlMs: 10 })).toBe("v1");

    // Wait past TTL so the next read is stale.
    await new Promise((resolve) => setTimeout(resolve, 30));

    // Stale read returns v1 *immediately* even though TTL has expired.
    // Background refresh fires asynchronously — caller doesn't await it.
    expect(await swr("k", fetcher, { ttlMs: 10 })).toBe("v1");

    // Let the background fetch settle.
    await new Promise((resolve) => setTimeout(resolve, 30));

    // The refresh ran exactly once for the stale read; the v1 → v2
    // transition is observable by directly reading the cache (not by
    // calling swr again, which would just trigger another refresh).
    expect(fetcher).toHaveBeenCalledTimes(2);
  });

  it("invalidate drops matching entries so the next read recomputes", async () => {
    const fetcher = vi.fn().mockResolvedValue("v");
    await swr("k", fetcher);
    invalidate((key) => key === "k");
    await swr("k", fetcher);
    expect(fetcher).toHaveBeenCalledTimes(2);
  });
});
