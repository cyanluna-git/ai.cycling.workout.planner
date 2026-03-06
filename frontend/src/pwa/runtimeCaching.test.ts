import { describe, expect, it } from 'vitest'
import {
  API_CACHE_MAX_AGE_SECONDS,
  API_CACHE_MAX_ENTRIES,
  API_CACHE_TIMEOUT_SECONDS,
  authSensitiveApiRuntimeCaching,
  cacheableApiRuntimeCaching,
  isAuthSensitiveApiPath,
  isCacheableApiPath,
  pwaRuntimeCaching,
} from './runtimeCaching'

function matches(entry: { urlPattern: ({ url }: { url: URL }) => boolean }, pathname: string) {
  return entry.urlPattern({ url: new URL(pathname, 'https://example.com') })
}

describe('PWA runtime caching split', () => {
  it('marks auth and bootstrap routes as auth-sensitive', () => {
    expect(isAuthSensitiveApiPath('/api/settings')).toBe(true)
    expect(isAuthSensitiveApiPath('/api/auth/intervals/status')).toBe(true)
    expect(isAuthSensitiveApiPath('/api/auth/intervals/url')).toBe(true)
    expect(isAuthSensitiveApiPath('/api/fitness')).toBe(false)
  })

  it('keeps only non-auth API routes on the cached path', () => {
    expect(isCacheableApiPath('/api/fitness')).toBe(true)
    expect(isCacheableApiPath('/api/workout/today')).toBe(true)
    expect(isCacheableApiPath('/api/settings')).toBe(false)
    expect(isCacheableApiPath('/api/auth/intervals/status')).toBe(false)
    expect(isCacheableApiPath('/health')).toBe(false)
  })

  it('uses NetworkOnly for auth-sensitive routes and preserves NetworkFirst for the rest', () => {
    expect(pwaRuntimeCaching).toHaveLength(2)
    expect(authSensitiveApiRuntimeCaching.handler).toBe('NetworkOnly')
    expect(cacheableApiRuntimeCaching.handler).toBe('NetworkFirst')

    expect(matches(authSensitiveApiRuntimeCaching, '/api/settings')).toBe(true)
    expect(matches(authSensitiveApiRuntimeCaching, '/api/auth/intervals/disconnect')).toBe(true)
    expect(matches(authSensitiveApiRuntimeCaching, '/api/fitness')).toBe(false)

    expect(matches(cacheableApiRuntimeCaching, '/api/fitness')).toBe(true)
    expect(matches(cacheableApiRuntimeCaching, '/api/workout/today')).toBe(true)
    expect(matches(cacheableApiRuntimeCaching, '/api/settings')).toBe(false)
    expect(matches(cacheableApiRuntimeCaching, '/api/auth/intervals/status')).toBe(false)
  })

  it('keeps the explicit cached API timeout and expiration settings for non-auth routes', () => {
    expect(cacheableApiRuntimeCaching.options).toEqual({
      cacheName: 'api-cache',
      expiration: {
        maxEntries: API_CACHE_MAX_ENTRIES,
        maxAgeSeconds: API_CACHE_MAX_AGE_SECONDS,
      },
      networkTimeoutSeconds: API_CACHE_TIMEOUT_SECONDS,
    })
  })
})
