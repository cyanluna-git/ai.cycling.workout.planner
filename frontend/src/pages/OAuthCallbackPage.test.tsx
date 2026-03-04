/**
 * Tests for OAuthCallbackPage — Intervals.icu OAuth 2.0 callback handler (task #266)
 *
 * Covers:
 * - i18n keys: oauth.* keys exist in both en.json and ko.json
 * - processing state: spinner renders while awaiting callback
 * - success state: CheckCircle renders after successful exchange
 * - error state: XCircle renders on OAuth denial, state mismatch, missing params, API error
 * - state mismatch: stored localStorage state !== URL state → error
 * - onComplete callback: called after timeout in each terminal state
 * - back button: renders in error state and calls onComplete
 * - api.ts: all 4 OAuth functions are exported
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { act, render, screen, waitFor } from '@testing-library/react'
import { OAuthCallbackPage } from './OAuthCallbackPage'
import * as api from '@/lib/api'
import enLocale from '../i18n/locales/en.json'
import koLocale from '../i18n/locales/ko.json'

// ---------------------------------------------------------------------------
// localStorage mock — vitest v4 jsdom provides a non-functional localStorage stub
// ---------------------------------------------------------------------------

type LocalStorageMock = {
    store: Map<string, string>
    getItem: (key: string) => string | null
    setItem: (key: string, value: string) => void
    removeItem: (key: string) => void
    clear: () => void
}

function createLocalStorageMock(): LocalStorageMock {
    const store = new Map<string, string>()
    return {
        store,
        getItem: (key: string) => store.get(key) ?? null,
        setItem: (key: string, value: string) => store.set(key, value),
        removeItem: (key: string) => store.delete(key),
        clear: () => store.clear(),
    }
}

// ---------------------------------------------------------------------------
// Helpers — control window.location.search via history API
// ---------------------------------------------------------------------------

function navigateTo(search: string) {
    window.history.pushState({}, '', search || '/')
}

function resetLocation() {
    window.history.pushState({}, '', '/')
}

// ---------------------------------------------------------------------------
// i18n locale key tests — oauth section
// ---------------------------------------------------------------------------

describe('i18n locale files — oauth keys', () => {
    const REQUIRED_KEYS = [
        'connectButton',
        'connected',
        'connectedVia',
        'disconnect',
        'disconnected',
        'connecting',
        'error',
        'denied',
        'manualApiKey',
        'processing',
        'success',
    ] as const

    for (const key of REQUIRED_KEYS) {
        it(`en.json has oauth.${key} as a non-empty string`, () => {
            const oauth = (enLocale as Record<string, unknown>).oauth as Record<string, unknown>
            expect(typeof oauth[key]).toBe('string')
            expect((oauth[key] as string).length).toBeGreaterThan(0)
        })

        it(`ko.json has oauth.${key} as a non-empty string`, () => {
            const oauth = (koLocale as Record<string, unknown>).oauth as Record<string, unknown>
            expect(typeof oauth[key]).toBe('string')
            expect((oauth[key] as string).length).toBeGreaterThan(0)
        })
    }

    it('en.json oauth keys do not contain emoji characters', () => {
        const oauth = (enLocale as Record<string, unknown>).oauth as Record<string, unknown>
        for (const key of REQUIRED_KEYS) {
            expect(/[\u{1F000}-\u{1FFFF}]/u.test(oauth[key] as string)).toBe(false)
        }
    })

    it('ko.json oauth keys do not contain emoji characters', () => {
        const oauth = (koLocale as Record<string, unknown>).oauth as Record<string, unknown>
        for (const key of REQUIRED_KEYS) {
            expect(/[\u{1F000}-\u{1FFFF}]/u.test(oauth[key] as string)).toBe(false)
        }
    })
})

// ---------------------------------------------------------------------------
// api.ts — OAuth function exports
// ---------------------------------------------------------------------------

describe('api.ts — OAuth function exports', () => {
    it('exports fetchOAuthUrl as a function', () => {
        expect(typeof api.fetchOAuthUrl).toBe('function')
    })

    it('exports submitOAuthCallback as a function', () => {
        expect(typeof api.submitOAuthCallback).toBe('function')
    })

    it('exports disconnectOAuth as a function', () => {
        expect(typeof api.disconnectOAuth).toBe('function')
    })

    it('exports fetchOAuthStatus as a function', () => {
        expect(typeof api.fetchOAuthStatus).toBe('function')
    })
})

// ---------------------------------------------------------------------------
// OAuthCallbackPage — processing state (initial render, sync check)
// These tests use REAL timers since we assert on the INITIAL render only.
// ---------------------------------------------------------------------------

describe('OAuthCallbackPage — processing state (initial render)', () => {
    let mockStorage: LocalStorageMock

    beforeEach(() => {
        mockStorage = createLocalStorageMock()
        vi.stubGlobal('localStorage', mockStorage)
        // Mock API so it never resolves (keeps component in processing state)
        vi.spyOn(api, 'submitOAuthCallback').mockImplementation(
            () => new Promise(() => {}) // never resolves
        )
        mockStorage.setItem('intervals_oauth_state', 'state-abc')
        navigateTo('?code=auth-code-123&state=state-abc')
    })

    afterEach(() => {
        vi.restoreAllMocks()
        vi.unstubAllGlobals()
        resetLocation()
    })

    it('renders Loader2 spinner in processing state initially', () => {
        const { container } = render(
            <OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />
        )
        const spinner = container.querySelector('.animate-spin')
        expect(spinner).not.toBeNull()
    })

    it('renders processing text initially', () => {
        render(<OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />)
        expect(screen.getByText('Connecting to Intervals.icu...')).toBeInTheDocument()
    })
})

// ---------------------------------------------------------------------------
// OAuthCallbackPage — callback invocation
// ---------------------------------------------------------------------------

describe('OAuthCallbackPage — API callback invocation', () => {
    let mockStorage: LocalStorageMock

    beforeEach(() => {
        mockStorage = createLocalStorageMock()
        vi.stubGlobal('localStorage', mockStorage)
        vi.spyOn(api, 'submitOAuthCallback').mockResolvedValue({
            success: true,
            athlete_id: 'i12345',
        })
        mockStorage.setItem('intervals_oauth_state', 'state-abc')
        navigateTo('?code=auth-code-123&state=state-abc')
    })

    afterEach(() => {
        vi.restoreAllMocks()
        vi.unstubAllGlobals()
        resetLocation()
    })

    it('calls submitOAuthCallback with correct args', async () => {
        render(<OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />)
        await waitFor(() => {
            expect(api.submitOAuthCallback).toHaveBeenCalledWith(
                'token',
                'auth-code-123',
                'state-abc'
            )
        })
    })
})

// ---------------------------------------------------------------------------
// OAuthCallbackPage — success state (real timers for async resolution)
// ---------------------------------------------------------------------------

describe('OAuthCallbackPage — success state (async)', () => {
    let mockStorage: LocalStorageMock

    beforeEach(() => {
        mockStorage = createLocalStorageMock()
        vi.stubGlobal('localStorage', mockStorage)
        vi.spyOn(api, 'submitOAuthCallback').mockResolvedValue({
            success: true,
            athlete_id: 'i12345',
        })
        mockStorage.setItem('intervals_oauth_state', 'state-abc')
        navigateTo('?code=auth-code-123&state=state-abc')
    })

    afterEach(() => {
        vi.restoreAllMocks()
        vi.unstubAllGlobals()
        resetLocation()
    })

    it('renders success text after successful API call', async () => {
        render(<OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />)
        await waitFor(() => {
            expect(screen.getByText('Successfully connected!')).toBeInTheDocument()
        })
    })

    it('does NOT render spinner after success', async () => {
        const { container } = render(
            <OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />
        )
        await waitFor(() => {
            expect(screen.getByText('Successfully connected!')).toBeInTheDocument()
        })
        expect(container.querySelector('.animate-spin')).toBeNull()
    })

    it('removes intervals_oauth_state from localStorage after success', async () => {
        render(<OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />)
        await waitFor(() => {
            expect(screen.getByText('Successfully connected!')).toBeInTheDocument()
        })
        expect(mockStorage.getItem('intervals_oauth_state')).toBeNull()
    })

    it('does NOT show error message on success', async () => {
        render(<OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />)
        await waitFor(() => {
            expect(screen.getByText('Successfully connected!')).toBeInTheDocument()
        })
        expect(screen.queryByText(/Connection failed:/i)).toBeNull()
        expect(screen.queryByText('Access was denied.')).toBeNull()
    })

    it('does NOT render .text-destructive paragraph on success', async () => {
        const { container } = render(
            <OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />
        )
        await waitFor(() => {
            expect(screen.getByText('Successfully connected!')).toBeInTheDocument()
        })
        expect(container.querySelector('p.text-destructive')).toBeNull()
    })
})

// ---------------------------------------------------------------------------
// OAuthCallbackPage — success state timeout (fake timers for onComplete)
// ---------------------------------------------------------------------------

describe('OAuthCallbackPage — success state timeout', () => {
    let mockStorage: LocalStorageMock

    beforeEach(() => {
        vi.useFakeTimers()
        mockStorage = createLocalStorageMock()
        vi.stubGlobal('localStorage', mockStorage)
        vi.spyOn(api, 'submitOAuthCallback').mockResolvedValue({
            success: true,
            athlete_id: 'i12345',
        })
        mockStorage.setItem('intervals_oauth_state', 'state-abc')
        navigateTo('?code=auth-code-123&state=state-abc')
    })

    afterEach(() => {
        vi.runAllTimers()
        vi.useRealTimers()
        vi.restoreAllMocks()
        vi.unstubAllGlobals()
        resetLocation()
    })

    it('calls onComplete after 2000ms following success', async () => {
        const onComplete = vi.fn()
        render(<OAuthCallbackPage accessToken="token" onComplete={onComplete} />)
        // Allow the mock promise to resolve
        await act(async () => {
            await vi.runAllTimersAsync()
        })
        // Now advance past the 2000ms success redirect timer
        vi.advanceTimersByTime(2000)
        expect(onComplete).toHaveBeenCalledTimes(1)
    })
})

// ---------------------------------------------------------------------------
// OAuthCallbackPage — error: OAuth denial (synchronous, no async needed)
// ---------------------------------------------------------------------------

describe('OAuthCallbackPage — error: OAuth denial', () => {
    let mockStorage: LocalStorageMock

    beforeEach(() => {
        vi.useFakeTimers()
        mockStorage = createLocalStorageMock()
        vi.stubGlobal('localStorage', mockStorage)
        navigateTo('?error=access_denied')
    })

    afterEach(() => {
        vi.runAllTimers()
        vi.useRealTimers()
        vi.restoreAllMocks()
        vi.unstubAllGlobals()
        resetLocation()
    })

    it('renders "Access was denied." error message immediately', () => {
        render(<OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />)
        expect(screen.getByText('Access was denied.')).toBeInTheDocument()
    })

    it('does NOT call submitOAuthCallback when error param is present', () => {
        const spy = vi.spyOn(api, 'submitOAuthCallback')
        render(<OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />)
        expect(spy).not.toHaveBeenCalled()
    })

    it('renders a Back button in error state', () => {
        render(<OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />)
        const buttons = screen.getAllByRole('button')
        const backBtn = buttons.find((b) => /back/i.test(b.textContent ?? ''))
        expect(backBtn).toBeDefined()
    })

    it('calls onComplete when Back button is clicked', () => {
        const onComplete = vi.fn()
        render(<OAuthCallbackPage accessToken="token" onComplete={onComplete} />)
        const buttons = screen.getAllByRole('button')
        const backBtn = buttons.find((b) => /back/i.test(b.textContent ?? ''))!
        // Use act + fireEvent to avoid userEvent async issues with fake timers
        act(() => {
            backBtn.click()
        })
        expect(onComplete).toHaveBeenCalledTimes(1)
    })

    it('calls onComplete after 3000ms timeout on denial error', () => {
        const onComplete = vi.fn()
        render(<OAuthCallbackPage accessToken="token" onComplete={onComplete} />)
        expect(onComplete).not.toHaveBeenCalled()
        vi.advanceTimersByTime(3000)
        expect(onComplete).toHaveBeenCalledTimes(1)
    })

    it('does NOT show spinner in error state', () => {
        const { container } = render(
            <OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />
        )
        expect(container.querySelector('.animate-spin')).toBeNull()
    })
})

// ---------------------------------------------------------------------------
// OAuthCallbackPage — error: missing code or state
// ---------------------------------------------------------------------------

describe('OAuthCallbackPage — error: missing code or state', () => {
    let mockStorage: LocalStorageMock

    beforeEach(() => {
        vi.useFakeTimers()
        mockStorage = createLocalStorageMock()
        vi.stubGlobal('localStorage', mockStorage)
    })

    afterEach(() => {
        vi.runAllTimers()
        vi.useRealTimers()
        vi.restoreAllMocks()
        vi.unstubAllGlobals()
        resetLocation()
    })

    it('shows error when code param is missing', () => {
        navigateTo('?state=state-abc') // code missing
        render(<OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />)
        expect(screen.getByText(/Missing code or state/i)).toBeInTheDocument()
    })

    it('shows error when state param is missing', () => {
        navigateTo('?code=auth-code-123') // state missing
        render(<OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />)
        expect(screen.getByText(/Missing code or state/i)).toBeInTheDocument()
    })

    it('does NOT show processing text when params are missing', () => {
        navigateTo('?state=state-abc') // code missing
        render(<OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />)
        expect(screen.queryByText('Connecting to Intervals.icu...')).toBeNull()
    })

    it('does NOT call submitOAuthCallback when code is missing', () => {
        navigateTo('?state=state-abc')
        const spy = vi.spyOn(api, 'submitOAuthCallback')
        render(<OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />)
        expect(spy).not.toHaveBeenCalled()
    })

    it('calls onComplete after 3000ms when code is missing', () => {
        navigateTo('?state=state-abc')
        const onComplete = vi.fn()
        render(<OAuthCallbackPage accessToken="token" onComplete={onComplete} />)
        expect(onComplete).not.toHaveBeenCalled()
        vi.advanceTimersByTime(3000)
        expect(onComplete).toHaveBeenCalledTimes(1)
    })
})

// ---------------------------------------------------------------------------
// OAuthCallbackPage — error: state mismatch
// ---------------------------------------------------------------------------

describe('OAuthCallbackPage — error: state mismatch', () => {
    let mockStorage: LocalStorageMock

    beforeEach(() => {
        vi.useFakeTimers()
        mockStorage = createLocalStorageMock()
        vi.stubGlobal('localStorage', mockStorage)
        // URL has state "state-from-url", stored state is "different-state"
        mockStorage.setItem('intervals_oauth_state', 'different-state')
        navigateTo('?code=auth-code-123&state=state-from-url')
    })

    afterEach(() => {
        vi.runAllTimers()
        vi.useRealTimers()
        vi.restoreAllMocks()
        vi.unstubAllGlobals()
        resetLocation()
    })

    it('shows error message when stored state does not match URL state', () => {
        render(<OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />)
        expect(screen.getByText(/State mismatch/i)).toBeInTheDocument()
    })

    it('does NOT call submitOAuthCallback on state mismatch', () => {
        const spy = vi.spyOn(api, 'submitOAuthCallback')
        render(<OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />)
        expect(spy).not.toHaveBeenCalled()
    })

    it('renders a Back button on state mismatch error', () => {
        render(<OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />)
        const buttons = screen.getAllByRole('button')
        const backBtn = buttons.find((b) => /back/i.test(b.textContent ?? ''))
        expect(backBtn).toBeDefined()
    })

    it('calls onComplete after 3000ms on state mismatch error', () => {
        const onComplete = vi.fn()
        render(<OAuthCallbackPage accessToken="token" onComplete={onComplete} />)
        expect(onComplete).not.toHaveBeenCalled()
        vi.advanceTimersByTime(3000)
        expect(onComplete).toHaveBeenCalledTimes(1)
    })
})

// ---------------------------------------------------------------------------
// OAuthCallbackPage — no stored state: skips mismatch check, proceeds to API
// ---------------------------------------------------------------------------

describe('OAuthCallbackPage — no stored state skips mismatch check', () => {
    let mockStorage: LocalStorageMock

    beforeEach(() => {
        mockStorage = createLocalStorageMock()
        vi.stubGlobal('localStorage', mockStorage)
        vi.spyOn(api, 'submitOAuthCallback').mockResolvedValue({
            success: true,
            athlete_id: 'i99999',
        })
        // localStorage is empty (no stored state)
        navigateTo('?code=auth-code-456&state=state-xyz')
    })

    afterEach(() => {
        vi.restoreAllMocks()
        vi.unstubAllGlobals()
        resetLocation()
    })

    it('proceeds to call API when no stored state exists', async () => {
        render(<OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />)
        await waitFor(() => {
            expect(api.submitOAuthCallback).toHaveBeenCalledWith(
                'token',
                'auth-code-456',
                'state-xyz'
            )
        })
    })

    it('shows success after API call when no stored state', async () => {
        render(<OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />)
        await waitFor(() => {
            expect(screen.getByText('Successfully connected!')).toBeInTheDocument()
        })
    })
})

// ---------------------------------------------------------------------------
// OAuthCallbackPage — error: API call fails (async)
// ---------------------------------------------------------------------------

describe('OAuthCallbackPage — error: API call fails', () => {
    let mockStorage: LocalStorageMock

    beforeEach(() => {
        mockStorage = createLocalStorageMock()
        vi.stubGlobal('localStorage', mockStorage)
        vi.spyOn(api, 'submitOAuthCallback').mockRejectedValue(
            new Error('Invalid authorization code')
        )
        mockStorage.setItem('intervals_oauth_state', 'state-abc')
        navigateTo('?code=bad-code&state=state-abc')
    })

    afterEach(() => {
        vi.restoreAllMocks()
        vi.unstubAllGlobals()
        resetLocation()
    })

    it('shows error message when API call throws', async () => {
        render(<OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />)
        await waitFor(() => {
            expect(screen.getByText(/Invalid authorization code/i)).toBeInTheDocument()
        })
    })

    it('renders Back button after API failure', async () => {
        render(<OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />)
        await waitFor(() => {
            const buttons = screen.getAllByRole('button')
            const backBtn = buttons.find((b) => /back/i.test(b.textContent ?? ''))
            expect(backBtn).toBeDefined()
        })
    })

    it('calls onComplete after 3000ms following API failure', async () => {
        vi.useFakeTimers()
        vi.spyOn(api, 'submitOAuthCallback').mockRejectedValue(
            new Error('Invalid authorization code')
        )
        const onComplete = vi.fn()
        render(<OAuthCallbackPage accessToken="token" onComplete={onComplete} />)
        await act(async () => {
            await vi.runAllTimersAsync()
        })
        // Advance past the 3000ms redirect timer
        vi.advanceTimersByTime(3000)
        vi.useRealTimers()
        expect(onComplete).toHaveBeenCalledTimes(1)
    })

    it('shows "Unknown error" for non-Error rejection', async () => {
        vi.spyOn(api, 'submitOAuthCallback').mockRejectedValue('something-weird')
        render(<OAuthCallbackPage accessToken="token" onComplete={vi.fn()} />)
        await waitFor(() => {
            expect(screen.getByText(/Unknown error/i)).toBeInTheDocument()
        })
    })
})
