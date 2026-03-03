/**
 * Tests for queryCache utility (task #320)
 *
 * Covers:
 * - getCachedData: returns undefined when key absent
 * - getCachedData: returns stored value when fresh
 * - getCachedData: returns undefined and removes item when TTL expired
 * - getCachedData: returns undefined and does not throw when localStorage throws
 * - setCachedData: stores value under prefixed key with timestamp
 * - setCachedData: overwrites previous value
 * - setCachedData: does not throw when localStorage throws
 * - removeCachedData: removes the prefixed key from localStorage
 * - removeCachedData: is a no-op for a key that was never set
 * - removeCachedData: does not throw when localStorage throws
 * - getCachedData returns undefined after removeCachedData
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const CACHE_PREFIX = 'ai-coach-cache-'
const CACHE_TTL = 24 * 60 * 60 * 1000 // 24h in ms

// ---------------------------------------------------------------------------
// In-memory localStorage mock (jsdom in this vitest setup has no working
// localStorage — --localstorage-file warns with no valid path at runtime)
// ---------------------------------------------------------------------------

function makeLocalStorageMock() {
    const store: Record<string, string> = {}
    return {
        store,
        getItem: vi.fn((key: string) => store[key] ?? null),
        setItem: vi.fn((key: string, value: string) => { store[key] = value }),
        removeItem: vi.fn((key: string) => { delete store[key] }),
        clear: vi.fn(() => { Object.keys(store).forEach(k => delete store[k]) }),
    }
}

// Helper: read directly from the mock store
function getRaw(mock: ReturnType<typeof makeLocalStorageMock>, key: string): string | null {
    return mock.store[CACHE_PREFIX + key] ?? null
}

// ---------------------------------------------------------------------------
// Setup — replace global localStorage before each test
// ---------------------------------------------------------------------------

let lsMock: ReturnType<typeof makeLocalStorageMock>

beforeEach(() => {
    lsMock = makeLocalStorageMock()
    vi.stubGlobal('localStorage', lsMock)
})

afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
})

// We import AFTER stubbing so the module picks up the mock on first load.
// But since the module is already loaded (ES module cache), we rely on the
// fact that the module accesses `localStorage` at call time (not at import
// time), so the stub is in effect when the functions run.

// eslint-disable-next-line @typescript-eslint/consistent-type-imports
import { getCachedData, setCachedData, removeCachedData } from './queryCache'

// ---------------------------------------------------------------------------
// getCachedData
// ---------------------------------------------------------------------------

describe('getCachedData', () => {
    it('returns undefined when key is absent', () => {
        expect(getCachedData('no-such-key')).toBeUndefined()
    })

    it('returns the stored value when within TTL', () => {
        const now = Date.now()
        lsMock.store[CACHE_PREFIX + 'myKey'] = JSON.stringify({ data: { val: 42 }, timestamp: now })

        expect(getCachedData<{ val: number }>('myKey')).toEqual({ val: 42 })
    })

    it('returns undefined and removes the item when TTL has expired', () => {
        const expired = Date.now() - (CACHE_TTL + 1)
        lsMock.store[CACHE_PREFIX + 'stale'] = JSON.stringify({ data: { val: 99 }, timestamp: expired })

        const result = getCachedData('stale')
        expect(result).toBeUndefined()
        // Item should have been pruned via removeItem
        expect(lsMock.removeItem).toHaveBeenCalledWith(CACHE_PREFIX + 'stale')
        expect(getRaw(lsMock, 'stale')).toBeNull()
    })

    it('returns undefined when localStorage.getItem throws', () => {
        lsMock.getItem.mockImplementationOnce(() => {
            throw new Error('SecurityError')
        })
        expect(getCachedData('anyKey')).toBeUndefined()
    })

    it('returns undefined when stored JSON is malformed', () => {
        lsMock.store[CACHE_PREFIX + 'bad'] = 'not-json'
        expect(getCachedData('bad')).toBeUndefined()
    })
})

// ---------------------------------------------------------------------------
// setCachedData
// ---------------------------------------------------------------------------

describe('setCachedData', () => {
    it('stores the value under the prefixed key with a timestamp', () => {
        setCachedData('fitness', { ctl: 55 })

        expect(lsMock.setItem).toHaveBeenCalledWith(
            CACHE_PREFIX + 'fitness',
            expect.any(String)
        )
        const raw = getRaw(lsMock, 'fitness')
        expect(raw).not.toBeNull()
        const parsed = JSON.parse(raw!)
        expect(parsed.data).toEqual({ ctl: 55 })
        expect(typeof parsed.timestamp).toBe('number')
    })

    it('overwrites a previously stored value', () => {
        setCachedData('counter', 1)
        setCachedData('counter', 2)

        const raw = getRaw(lsMock, 'counter')!
        expect(JSON.parse(raw).data).toBe(2)
    })

    it('does not throw when localStorage.setItem throws', () => {
        lsMock.setItem.mockImplementationOnce(() => {
            throw new Error('QuotaExceededError')
        })
        expect(() => setCachedData('safe', { a: 1 })).not.toThrow()
    })
})

// ---------------------------------------------------------------------------
// removeCachedData
// ---------------------------------------------------------------------------

describe('removeCachedData', () => {
    it('removes the prefixed key from localStorage', () => {
        setCachedData('todayPlan', { planned_tss: 80 })
        expect(getRaw(lsMock, 'todayPlan')).not.toBeNull()

        removeCachedData('todayPlan')

        expect(lsMock.removeItem).toHaveBeenCalledWith(CACHE_PREFIX + 'todayPlan')
        expect(getRaw(lsMock, 'todayPlan')).toBeNull()
    })

    it('is a no-op when the key was never set (does not throw)', () => {
        expect(() => removeCachedData('never-set')).not.toThrow()
        // removeItem should still be called (just a no-op at the store level)
        expect(lsMock.removeItem).toHaveBeenCalledWith(CACHE_PREFIX + 'never-set')
    })

    it('does not affect a different key with a similar name', () => {
        setCachedData('todayPlan', { planned_tss: 80 })
        setCachedData('todayPlanExtra', { planned_tss: 60 })

        removeCachedData('todayPlan')

        expect(getRaw(lsMock, 'todayPlan')).toBeNull()
        expect(getRaw(lsMock, 'todayPlanExtra')).not.toBeNull()
    })

    it('getCachedData returns undefined after removeCachedData is called', () => {
        const now = Date.now()
        lsMock.store[CACHE_PREFIX + 'todayPlan'] = JSON.stringify({
            data: { weekly_tss_target: 400 },
            timestamp: now,
        })
        expect(getCachedData<{ weekly_tss_target: number }>('todayPlan')).toEqual({ weekly_tss_target: 400 })

        removeCachedData('todayPlan')
        expect(getCachedData('todayPlan')).toBeUndefined()
    })

    it('does not throw when localStorage.removeItem throws', () => {
        lsMock.removeItem.mockImplementationOnce(() => {
            throw new Error('SecurityError')
        })
        expect(() => removeCachedData('anyKey')).not.toThrow()
    })

    it('getCachedData returns undefined after removal even when item was fresh', () => {
        const now = Date.now()
        lsMock.store[CACHE_PREFIX + 'fresh'] = JSON.stringify({ data: { x: 1 }, timestamp: now })

        removeCachedData('fresh')
        expect(getCachedData('fresh')).toBeUndefined()
    })
})

// ---------------------------------------------------------------------------
// Cross-function round-trip integration
// ---------------------------------------------------------------------------

describe('queryCache — round-trip', () => {
    it('set → get → remove → get returns undefined', () => {
        setCachedData('weeklyPlan', { total: 450 })

        // Reads back the freshly written value
        const stored = JSON.parse(getRaw(lsMock, 'weeklyPlan')!)
        lsMock.store[CACHE_PREFIX + 'weeklyPlan'] = JSON.stringify({ data: { total: 450 }, timestamp: stored.timestamp })
        expect(getCachedData<{ total: number }>('weeklyPlan')).toEqual({ total: 450 })

        removeCachedData('weeklyPlan')
        expect(getCachedData('weeklyPlan')).toBeUndefined()
    })

    it('remove does not bleed into unrelated keys', () => {
        const now = Date.now()
        lsMock.store[CACHE_PREFIX + 'fitness'] = JSON.stringify({ data: { ctl: 60 }, timestamp: now })
        lsMock.store[CACHE_PREFIX + 'weeklyCalendar'] = JSON.stringify({ data: { events: [] }, timestamp: now })

        removeCachedData('fitness')

        expect(getCachedData('fitness')).toBeUndefined()
        expect(getCachedData<{ events: unknown[] }>('weeklyCalendar')).toEqual({ events: [] })
    })

    it('multiple removes on same key are safe', () => {
        setCachedData('multi', { v: 1 })
        removeCachedData('multi')
        expect(() => removeCachedData('multi')).not.toThrow()
        expect(getCachedData('multi')).toBeUndefined()
    })
})
