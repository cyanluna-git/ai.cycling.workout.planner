/**
 * SWR utilities for AI Cycling Coach
 * 
 * Provides authenticated fetcher and common SWR configuration.
 * Vercel Best Practice: client-swr-dedup (automatic request deduplication)
 */

import i18n from '@/i18n/config';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Authenticated fetcher for SWR.
 * Automatically includes auth token and language headers.
 */
export function createAuthFetcher(token: string | undefined) {
    return async (url: string) => {
        const headers: HeadersInit = {
            'Accept-Language': i18n.language || 'ko',
            'Content-Type': 'application/json',
        };
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_BASE}${url}`, { headers });
        if (!response.ok) {
            const error = new Error('API request failed') as Error & { status: number };
            error.status = response.status;
            throw error;
        }
        return response.json();
    };
}

/**
 * Public fetcher (no auth required) for SWR.
 */
export async function publicFetcher(url: string) {
    const response = await fetch(`${API_BASE}${url}`);
    if (!response.ok) {
        const error = new Error('API request failed') as Error & { status: number };
        error.status = response.status;
        throw error;
    }
    return response.json();
}

/**
 * Default SWR configuration.
 * - dedupingInterval: 60s (prevent duplicate requests within 60 seconds)
 * - revalidateOnFocus: false (don't refetch on tab focus)
 * - errorRetryCount: 2 (retry up to 2 times on error)
 */
export const defaultSWRConfig = {
    dedupingInterval: 60000,
    revalidateOnFocus: false,
    errorRetryCount: 2,
};
