const CACHE_PREFIX = 'ai-coach-cache-';
const CACHE_TTL = 24 * 60 * 60 * 1000;

export function getCachedData<T>(key: string): T | undefined {
  try {
    const raw = localStorage.getItem(CACHE_PREFIX + key);
    if (!raw) return undefined;
    const { data, timestamp } = JSON.parse(raw);
    if (Date.now() - timestamp > CACHE_TTL) {
      localStorage.removeItem(CACHE_PREFIX + key);
      return undefined;
    }
    return data as T;
  } catch {
    return undefined;
  }
}

export function setCachedData<T>(key: string, data: T): void {
  try {
    localStorage.setItem(
      CACHE_PREFIX + key,
      JSON.stringify({ data, timestamp: Date.now() })
    );
  } catch {
    // Intentionally ignored -- localStorage may be full or disabled
  }
}
