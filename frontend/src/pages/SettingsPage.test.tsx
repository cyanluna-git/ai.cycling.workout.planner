import '../i18n/config'

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SettingsPage } from './SettingsPage'
import { queryKeys } from '@/lib/queryClient'
import * as authContext from '@/contexts/AuthContext'
import * as api from '@/lib/api'
import type { SettingsBootstrapResponse } from '@/lib/api'

vi.mock('@/contexts/AuthContext', () => ({
    useAuth: vi.fn(),
}))

vi.mock('@/lib/api', async () => {
    const actual = await vi.importActual<typeof import('@/lib/api')>('@/lib/api')
    return {
        ...actual,
        fetchSettingsBootstrap: vi.fn(),
        fetchOAuthUrl: vi.fn(),
        fetchOAuthStatus: vi.fn(),
        disconnectOAuth: vi.fn(),
    }
})

const mockUseAuth = vi.mocked(authContext.useAuth)
const mockFetchSettingsBootstrap = vi.mocked(api.fetchSettingsBootstrap)
const mockFetchOAuthStatus = vi.mocked(api.fetchOAuthStatus)
const mockDisconnectOAuth = vi.mocked(api.disconnectOAuth)

const connectedBootstrap: SettingsBootstrapResponse = {
    settings: {
        ftp: 250,
        max_hr: 185,
        lthr: 170,
        training_goal: 'Build fitness',
        exclude_barcode_workouts: false,
        training_style: 'auto',
        preferred_duration: 60,
        training_focus: 'maintain',
        weekly_tss_target: 400,
        weekly_availability: {
            "0": "available" as const,
            "1": "available" as const,
            "2": "available" as const,
            "3": "available" as const,
            "4": "available" as const,
            "5": "available" as const,
            "6": "available" as const,
        },
    },
    api_keys_configured: true,
    intervals_connection: {
        connected: true,
        method: 'oauth',
        athlete_id: 'i154786',
    },
}

const disconnectedBootstrap = {
    ...connectedBootstrap,
    api_keys_configured: false,
    intervals_connection: {
        connected: false,
        method: 'none',
        athlete_id: null,
    },
}

function createQueryClient() {
    return new QueryClient({
        defaultOptions: {
            queries: {
                retry: false,
                gcTime: 0,
            },
        },
    })
}

function renderSettingsPage(queryClient: QueryClient) {
    return render(
        <QueryClientProvider client={queryClient}>
            <SettingsPage onBack={vi.fn()} />
        </QueryClientProvider>
    )
}

describe('SettingsPage', () => {
    beforeEach(() => {
        vi.stubGlobal('ResizeObserver', class {
            observe() {}
            unobserve() {}
            disconnect() {}
        })
        mockUseAuth.mockReturnValue({
            user: null,
            session: { access_token: 'token-123' } as never,
            loading: false,
            signUp: vi.fn(),
            signIn: vi.fn(),
            signInWithGoogle: vi.fn(),
            signOut: vi.fn(),
            resetPassword: vi.fn(),
        })
        mockFetchOAuthStatus.mockResolvedValue({
            connected: false,
            method: 'none',
            athlete_id: null,
        })
        mockDisconnectOAuth.mockResolvedValue({ success: true })
    })

    afterEach(() => {
        vi.clearAllMocks()
        vi.unstubAllGlobals()
    })

    it('does not show the connect button while bootstrap connection state is still loading', () => {
        const queryClient = createQueryClient()
        mockFetchSettingsBootstrap.mockImplementation(() => new Promise(() => {}))

        renderSettingsPage(queryClient)

        expect(screen.queryByRole('button', { name: /connect with intervals\.icu/i })).toBeNull()
        expect(mockFetchOAuthStatus).not.toHaveBeenCalled()
        expect(screen.getAllByText('Loading...').length).toBeGreaterThan(0)
    })

    it('renders the connected state from /api/settings bootstrap data', async () => {
        const queryClient = createQueryClient()
        mockFetchSettingsBootstrap.mockResolvedValue(connectedBootstrap)

        renderSettingsPage(queryClient)

        await waitFor(() => {
            expect(screen.getByText('Successfully connected to Intervals.icu.')).toBeInTheDocument()
        })

        expect(screen.queryByRole('button', { name: /connect with intervals\.icu/i })).toBeNull()
        const connectionLines = screen.getAllByText((_, element) => element?.textContent?.includes('Connected via OAuth') ?? false)
        expect(connectionLines[0]).toHaveTextContent('i154786')
        expect(screen.getByRole('button', { name: /disconnect/i })).toBeInTheDocument()
        expect(mockFetchOAuthStatus).not.toHaveBeenCalled()
    })

    it('renders the disconnected state from /api/settings bootstrap data', async () => {
        const queryClient = createQueryClient()
        mockFetchSettingsBootstrap.mockResolvedValue(disconnectedBootstrap)

        renderSettingsPage(queryClient)

        await waitFor(() => {
            expect(screen.getByRole('button', { name: /connect with intervals\.icu/i })).toBeInTheDocument()
        })

        const statusLines = screen.getAllByText((_, element) => element?.textContent?.includes('Not configured') ?? false)
        expect(statusLines[0]).toHaveTextContent('Status:')
    })

    it('updates the UI and shared query cache after disconnect', async () => {
        const user = userEvent.setup()
        const queryClient = createQueryClient()
        mockFetchSettingsBootstrap.mockResolvedValue(connectedBootstrap)

        renderSettingsPage(queryClient)

        await waitFor(() => {
            expect(screen.getByRole('button', { name: /disconnect/i })).toBeInTheDocument()
        })

        await user.click(screen.getByRole('button', { name: /disconnect/i }))

        await waitFor(() => {
            expect(screen.getByRole('button', { name: /connect with intervals\.icu/i })).toBeInTheDocument()
        })

        expect(mockDisconnectOAuth).toHaveBeenCalledWith('token-123')
        expect(queryClient.getQueryData(queryKeys.settingsBootstrap())).toMatchObject({
            api_keys_configured: false,
            intervals_connection: {
                connected: false,
                method: 'none',
                athlete_id: null,
            },
        })
    })
})
