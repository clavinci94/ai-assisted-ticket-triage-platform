/**
 * Tiny stale-while-revalidate cache for read-only API calls.
 *
 * Why this exists: Render Free + Neon Free Postgres have cold-starts.
 * Every navigation between Übersicht ↔ Workbench refires the same
 * fetches, each waiting for the (possibly cold) database. With this
 * cache, the second navigation gets the previous response instantly
 * and triggers a background refresh; the user sees real data within
 * milliseconds instead of seconds.
 *
 * Contract:
 *   - get(key)            → cached value or undefined
 *   - swr(key, fetchFn, { ttlMs })
 *       → returns cached value immediately if fresh OR stale,
 *         AND fires fetchFn in the background to update.
 *       → if no cached value exists, awaits fetchFn.
 *   - invalidate(predicate) → drop entries matching predicate
 *   - clear()              → drop all entries
 *
 * Not a replacement for React Query — just enough caching to make a
 * single-user demo feel snappy without adding a dependency.
 */

const store = new Map();
const inflight = new Map();

const DEFAULT_TTL = 30_000;

function now() {
  return Date.now();
}

export function get(key) {
  const entry = store.get(key);
  if (!entry) return undefined;
  return entry.value;
}

export async function swr(key, fetchFn, { ttlMs = DEFAULT_TTL } = {}) {
  const entry = store.get(key);
  const fresh = entry && now() - entry.fetchedAt < ttlMs;

  if (entry && fresh) {
    // Fully fresh — no refresh needed.
    return entry.value;
  }

  if (entry && !fresh) {
    // Stale — return immediately, refresh in the background.
    refreshInBackground(key, fetchFn);
    return entry.value;
  }

  // Cold cache — must wait. Dedupe parallel callers.
  if (inflight.has(key)) {
    return inflight.get(key);
  }
  const promise = fetchFn()
    .then((value) => {
      store.set(key, { value, fetchedAt: now() });
      return value;
    })
    .finally(() => {
      inflight.delete(key);
    });
  inflight.set(key, promise);
  return promise;
}

function refreshInBackground(key, fetchFn) {
  if (inflight.has(key)) return;
  const promise = fetchFn()
    .then((value) => {
      store.set(key, { value, fetchedAt: now() });
      return value;
    })
    .catch(() => {
      // Swallow — we still have stale data, leaving it is better than
      // discarding everything because of a transient blip.
    })
    .finally(() => {
      inflight.delete(key);
    });
  inflight.set(key, promise);
}

export function invalidate(predicate) {
  for (const key of [...store.keys()]) {
    if (predicate(key)) store.delete(key);
  }
  for (const key of [...inflight.keys()]) {
    if (predicate(key)) inflight.delete(key);
  }
}

export function clear() {
  store.clear();
  inflight.clear();
}
