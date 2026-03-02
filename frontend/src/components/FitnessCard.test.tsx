/**
 * Tests for FitnessCard component — Wellness manual sync button (task #223)
 *
 * Covers:
 * - i18n keys: fitness.refresh, fitness.refreshSuccess, fitness.refreshFailed
 *   exist in both en.json and ko.json
 * - Refresh button renders when onRefresh prop is provided
 * - Refresh button does NOT render when onRefresh is undefined
 * - Button is disabled when isRefreshing=true
 * - Button click calls the onRefresh callback
 * - RefreshCw icon has animate-spin class when isRefreshing=true
 * - RefreshCw icon does NOT have animate-spin when isRefreshing=false
 * - aria-label is set to fitness.refresh i18n key value
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FitnessCard } from './FitnessCard'
import type { TrainingMetrics, WellnessMetrics, AthleteProfile } from '@/lib/api'
import enLocale from '../i18n/locales/en.json'
import koLocale from '../i18n/locales/ko.json'

// ---------------------------------------------------------------------------
// Shared mock data
// ---------------------------------------------------------------------------

const mockTraining: TrainingMetrics = {
    ctl: 55.2,
    atl: 48.7,
    tsb: 6.5,
    form_status: 'Moderate',
}

const mockWellness: WellnessMetrics = {
    readiness: 'Good',
    hrv: 72,
    hrv_sdnn: null,
    rhr: 52,
    sleep_hours: 7.5,
    sleep_score: null,
    sleep_quality: null,
    weight: 70,
    body_fat: null,
    vo2max: null,
    soreness: null,
    fatigue: null,
    stress: null,
    mood: null,
    motivation: null,
    spo2: null,
    systolic: null,
    diastolic: null,
    respiration: null,
    readiness_score: null,
}

const mockProfile: AthleteProfile = {
    ftp: 250,
    max_hr: 185,
    lthr: 165,
    weight: 70,
    w_per_kg: 3.57,
    vo2max: 52.3,
}

// ---------------------------------------------------------------------------
// i18n locale key tests (static JSON inspection — no React required)
// ---------------------------------------------------------------------------

describe('i18n locale files — fitness refresh keys', () => {
    it('en.json has fitness.refresh as a non-empty string', () => {
        const fitness = (enLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect(typeof fitness.refresh).toBe('string')
        expect((fitness.refresh as string).length).toBeGreaterThan(0)
    })

    it('en.json has fitness.refreshSuccess as a non-empty string', () => {
        const fitness = (enLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect(typeof fitness.refreshSuccess).toBe('string')
        expect((fitness.refreshSuccess as string).length).toBeGreaterThan(0)
    })

    it('en.json has fitness.refreshFailed as a non-empty string', () => {
        const fitness = (enLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect(typeof fitness.refreshFailed).toBe('string')
        expect((fitness.refreshFailed as string).length).toBeGreaterThan(0)
    })

    it('ko.json has fitness.refresh as a non-empty string', () => {
        const fitness = (koLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect(typeof fitness.refresh).toBe('string')
        expect((fitness.refresh as string).length).toBeGreaterThan(0)
    })

    it('ko.json has fitness.refreshSuccess as a non-empty string', () => {
        const fitness = (koLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect(typeof fitness.refreshSuccess).toBe('string')
        expect((fitness.refreshSuccess as string).length).toBeGreaterThan(0)
    })

    it('ko.json has fitness.refreshFailed as a non-empty string', () => {
        const fitness = (koLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect(typeof fitness.refreshFailed).toBe('string')
        expect((fitness.refreshFailed as string).length).toBeGreaterThan(0)
    })

    it('en.json fitness.refresh does not contain emoji characters', () => {
        const fitness = (enLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect(/[\u{1F000}-\u{1FFFF}]/u.test(fitness.refresh as string)).toBe(false)
    })

    it('ko.json fitness.refresh does not contain emoji characters', () => {
        const fitness = (koLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect(/[\u{1F000}-\u{1FFFF}]/u.test(fitness.refresh as string)).toBe(false)
    })
})

// ---------------------------------------------------------------------------
// FitnessCard component — refresh button rendering
// ---------------------------------------------------------------------------

describe('FitnessCard — refresh button', () => {
    // -----------------------------------------------------------------------
    // Button presence / absence
    // -----------------------------------------------------------------------

    it('renders a button with aria-label "Refresh fitness data" when onRefresh is provided', () => {
        const onRefresh = vi.fn()
        render(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
                onRefresh={onRefresh}
            />
        )
        const btn = screen.getByRole('button', { name: /refresh fitness data/i })
        expect(btn).toBeInTheDocument()
    })

    it('does NOT render the refresh button when onRefresh prop is undefined', () => {
        render(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
            />
        )
        // aria-label comes from i18n fitness.refresh = "Refresh fitness data"
        const btn = screen.queryByRole('button', { name: /refresh fitness data/i })
        expect(btn).toBeNull()
    })

    it('does NOT render the refresh button when onRefresh is not passed (no isRefreshing either)', () => {
        const { container } = render(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
            />
        )
        // The button only mounts when onRefresh is truthy — verify at DOM level
        const buttons = container.querySelectorAll('button')
        expect(buttons.length).toBe(0)
    })

    // -----------------------------------------------------------------------
    // Button click
    // -----------------------------------------------------------------------

    it('calls onRefresh callback exactly once when button is clicked', async () => {
        const user = userEvent.setup()
        const onRefresh = vi.fn()
        render(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
                onRefresh={onRefresh}
                isRefreshing={false}
            />
        )
        const btn = screen.getByRole('button', { name: /refresh fitness data/i })
        await user.click(btn)
        expect(onRefresh).toHaveBeenCalledTimes(1)
    })

    it('does not call onRefresh when button is disabled (isRefreshing=true)', async () => {
        const user = userEvent.setup()
        const onRefresh = vi.fn()
        render(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
                onRefresh={onRefresh}
                isRefreshing={true}
            />
        )
        const btn = screen.getByRole('button', { name: /refresh fitness data/i })
        await user.click(btn)
        // Disabled buttons do not fire click handlers
        expect(onRefresh).not.toHaveBeenCalled()
    })

    // -----------------------------------------------------------------------
    // Button disabled state
    // -----------------------------------------------------------------------

    it('button is disabled when isRefreshing=true', () => {
        render(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
                onRefresh={vi.fn()}
                isRefreshing={true}
            />
        )
        const btn = screen.getByRole('button', { name: /refresh fitness data/i })
        expect(btn).toBeDisabled()
    })

    it('button is NOT disabled when isRefreshing=false', () => {
        render(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
                onRefresh={vi.fn()}
                isRefreshing={false}
            />
        )
        const btn = screen.getByRole('button', { name: /refresh fitness data/i })
        expect(btn).not.toBeDisabled()
    })

    it('button is NOT disabled when isRefreshing is omitted (defaults to undefined/falsy)', () => {
        render(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
                onRefresh={vi.fn()}
            />
        )
        const btn = screen.getByRole('button', { name: /refresh fitness data/i })
        expect(btn).not.toBeDisabled()
    })

    // -----------------------------------------------------------------------
    // RefreshCw icon animation
    // -----------------------------------------------------------------------

    it('RefreshCw icon has animate-spin class when isRefreshing=true', () => {
        const { container } = render(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
                onRefresh={vi.fn()}
                isRefreshing={true}
            />
        )
        // The SVG icon is inside the button; look for the element with animate-spin
        const spinningIcon = container.querySelector('.animate-spin')
        expect(spinningIcon).not.toBeNull()
    })

    it('RefreshCw icon does NOT have animate-spin class when isRefreshing=false', () => {
        const { container } = render(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
                onRefresh={vi.fn()}
                isRefreshing={false}
            />
        )
        const spinningIcon = container.querySelector('.animate-spin')
        expect(spinningIcon).toBeNull()
    })

    it('RefreshCw icon does NOT have animate-spin when isRefreshing is not passed', () => {
        const { container } = render(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
                onRefresh={vi.fn()}
            />
        )
        const spinningIcon = container.querySelector('.animate-spin')
        expect(spinningIcon).toBeNull()
    })

    // -----------------------------------------------------------------------
    // Button sizing / ghost variant
    // -----------------------------------------------------------------------

    it('refresh button has h-8 w-8 size classes', () => {
        const { container } = render(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
                onRefresh={vi.fn()}
            />
        )
        const btn = container.querySelector('button.h-8.w-8')
        expect(btn).not.toBeNull()
    })

    // -----------------------------------------------------------------------
    // Re-entry guard: button stays disabled while already refreshing
    // -----------------------------------------------------------------------

    it('button remains disabled if isRefreshing is still true after re-render', () => {
        const onRefresh = vi.fn()
        const { rerender } = render(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
                onRefresh={onRefresh}
                isRefreshing={false}
            />
        )
        // Simulate refresh starting
        rerender(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
                onRefresh={onRefresh}
                isRefreshing={true}
            />
        )
        const btn = screen.getByRole('button', { name: /refresh fitness data/i })
        expect(btn).toBeDisabled()

        // Simulate refresh completing
        rerender(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
                onRefresh={onRefresh}
                isRefreshing={false}
            />
        )
        expect(btn).not.toBeDisabled()
    })
})

// ---------------------------------------------------------------------------
// FitnessCard component — existing props unaffected (regression)
// ---------------------------------------------------------------------------

describe('FitnessCard — existing content not broken by refresh addition', () => {
    it('still renders the card title "Today\'s Condition"', () => {
        render(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
            />
        )
        expect(screen.getByText("Today's Condition")).toBeInTheDocument()
    })

    it('renders CTL value', () => {
        render(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
            />
        )
        expect(screen.getByText('55.2')).toBeInTheDocument()
    })

    it('renders ATL value', () => {
        render(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
            />
        )
        expect(screen.getByText('48.7')).toBeInTheDocument()
    })

    it('renders FTP value when provided', () => {
        render(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
            />
        )
        expect(screen.getByText('250W')).toBeInTheDocument()
    })

    it('renders readiness value', () => {
        render(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
            />
        )
        expect(screen.getByText('Good')).toBeInTheDocument()
    })

    it('renders both refresh button and card content together', () => {
        const onRefresh = vi.fn()
        render(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
                onRefresh={onRefresh}
                isRefreshing={false}
            />
        )
        expect(screen.getByRole('button', { name: /refresh fitness data/i })).toBeInTheDocument()
        expect(screen.getByText("Today's Condition")).toBeInTheDocument()
        expect(screen.getByText('250W')).toBeInTheDocument()
    })
})
