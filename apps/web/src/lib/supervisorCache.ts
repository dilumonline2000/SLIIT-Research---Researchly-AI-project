// Module-level singleton cache — survives Next.js client-side page navigations
// within the same browser tab. Resets on full page reload.
const _store = new Map<string, { data: unknown; ts: number }>();
const DEFAULT_TTL_MS = 5 * 60 * 1000; // 5 minutes

export function getCache<T>(key: string, ttl = DEFAULT_TTL_MS): T | null {
  const entry = _store.get(key);
  if (!entry) return null;
  if (Date.now() - entry.ts > ttl) {
    _store.delete(key);
    return null;
  }
  return entry.data as T;
}

export function setCache<T>(key: string, data: T): void {
  _store.set(key, { data, ts: Date.now() });
}

export function invalidateCache(...keys: string[]): void {
  if (keys.length === 0) {
    _store.clear();
  } else {
    keys.forEach((k) => _store.delete(k));
  }
}
