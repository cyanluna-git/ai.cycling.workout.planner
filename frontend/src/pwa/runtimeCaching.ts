type WorkboxRouteContext = {
  url: URL
}

export const AUTH_SENSITIVE_API_PATHS = ['/api/settings'] as const
export const AUTH_SENSITIVE_API_PREFIXES = ['/api/auth/'] as const

export const API_CACHE_TIMEOUT_SECONDS = 10
export const API_CACHE_MAX_ENTRIES = 50
export const API_CACHE_MAX_AGE_SECONDS = 60 * 60

export function isApiPath(pathname: string): boolean {
  return pathname.startsWith('/api/')
}

export function isAuthSensitiveApiPath(pathname: string): boolean {
  return (
    AUTH_SENSITIVE_API_PATHS.includes(pathname as (typeof AUTH_SENSITIVE_API_PATHS)[number]) ||
    AUTH_SENSITIVE_API_PREFIXES.some((prefix) => pathname.startsWith(prefix))
  )
}

export function isCacheableApiPath(pathname: string): boolean {
  return isApiPath(pathname) && !isAuthSensitiveApiPath(pathname)
}

// Auth/bootstrap requests should always resolve against the network immediately
// instead of waiting behind the shared NetworkFirst API timeout window.
export const authSensitiveApiRuntimeCaching = {
  urlPattern: ({ url }: WorkboxRouteContext) => isAuthSensitiveApiPath(url.pathname),
  handler: 'NetworkOnly' as const,
}

export const cacheableApiRuntimeCaching = {
  urlPattern: ({ url }: WorkboxRouteContext) => isCacheableApiPath(url.pathname),
  handler: 'NetworkFirst' as const,
  options: {
    cacheName: 'api-cache',
    expiration: {
      maxEntries: API_CACHE_MAX_ENTRIES,
      maxAgeSeconds: API_CACHE_MAX_AGE_SECONDS,
    },
    networkTimeoutSeconds: API_CACHE_TIMEOUT_SECONDS,
  },
}

export const pwaRuntimeCaching = [
  authSensitiveApiRuntimeCaching,
  cacheableApiRuntimeCaching,
]
