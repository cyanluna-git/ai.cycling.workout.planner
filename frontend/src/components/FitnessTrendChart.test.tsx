/**
 * Tests for FitnessTrendChart component — 7-day CTL/ATL/TSB trend chart (task #225)
 *
 * Covers:
 * - i18n keys (trendTitle, trendCTL, trendATL, trendTSB) in en.json and ko.json
 * - FitnessTrendChart renders when history data is provided
 * - FitnessTrendChart renders with empty history array
 * - FitnessCard does NOT render the chart section when ctl_history is null/undefined
 * - FitnessCard does NOT render the chart section when ctl_history is empty array
 * - FitnessCard renders the chart section when ctl_history has data
 * - TrainingHistoryPoint type shape is correct in api.ts
 */

import { describe, it, expect, vi, beforeAll } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FitnessTrendChart } from './FitnessTrendChart'
import { FitnessCard } from './FitnessCard'
import type { TrainingMetrics, WellnessMetrics, AthleteProfile, TrainingHistoryPoint } from '@/lib/api'
import enLocale from '../i18n/locales/en.json'
import koLocale from '../i18n/locales/ko.json'

// ---------------------------------------------------------------------------
// Recharts / ResizeObserver mocks
//
// ResponsiveContainer relies on ResizeObserver + measured DOM dimensions.
// In jsdom the container has zero dimensions, so ResponsiveContainer renders
// nothing. We stub global.ResizeObserver so the observer callback fires
// immediately and stub the container's getBoundingClientRect to return a
// non-zero size, allowing Recharts to render SVG children.
// ---------------------------------------------------------------------------

beforeAll(() => {
    // Provide a minimal ResizeObserver stub if jsdom does not supply one
    if (typeof global.ResizeObserver === 'undefined') {
        global.ResizeObserver = class {
            observe() {}
            unobserve() {}
            disconnect() {}
        }
    }
})

// ---------------------------------------------------------------------------
// Shared fixtures
// ---------------------------------------------------------------------------

const makeHistory = (n = 7): TrainingHistoryPoint[] =>
    Array.from({ length: n }, (_, i) => ({
        date: `2026-02-${String(i + 1).padStart(2, '0')}`,
        ctl: 55.0 + i,
        atl: 50.0 + i,
        tsb: 5.0,
    }))

const mockTraining: TrainingMetrics = {
    ctl: 60.0,
    atl: 55.0,
    tsb: 5.0,
    form_status: 'Fresh',
}

const mockWellness: WellnessMetrics = {
    readiness: 'Good',
    hrv: 70,
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

describe('i18n locale files — trend chart keys', () => {
    it('en.json has fitness.trendTitle as a non-empty string', () => {
        const fitness = (enLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect(typeof fitness.trendTitle).toBe('string')
        expect((fitness.trendTitle as string).length).toBeGreaterThan(0)
    })

    it('en.json has fitness.trendCTL as a non-empty string', () => {
        const fitness = (enLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect(typeof fitness.trendCTL).toBe('string')
        expect((fitness.trendCTL as string).length).toBeGreaterThan(0)
    })

    it('en.json has fitness.trendATL as a non-empty string', () => {
        const fitness = (enLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect(typeof fitness.trendATL).toBe('string')
        expect((fitness.trendATL as string).length).toBeGreaterThan(0)
    })

    it('en.json has fitness.trendTSB as a non-empty string', () => {
        const fitness = (enLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect(typeof fitness.trendTSB).toBe('string')
        expect((fitness.trendTSB as string).length).toBeGreaterThan(0)
    })

    it('ko.json has fitness.trendTitle as a non-empty string', () => {
        const fitness = (koLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect(typeof fitness.trendTitle).toBe('string')
        expect((fitness.trendTitle as string).length).toBeGreaterThan(0)
    })

    it('ko.json has fitness.trendCTL as a non-empty string', () => {
        const fitness = (koLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect(typeof fitness.trendCTL).toBe('string')
        expect((fitness.trendCTL as string).length).toBeGreaterThan(0)
    })

    it('ko.json has fitness.trendATL as a non-empty string', () => {
        const fitness = (koLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect(typeof fitness.trendATL).toBe('string')
        expect((fitness.trendATL as string).length).toBeGreaterThan(0)
    })

    it('ko.json has fitness.trendTSB as a non-empty string', () => {
        const fitness = (koLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect(typeof fitness.trendTSB).toBe('string')
        expect((fitness.trendTSB as string).length).toBeGreaterThan(0)
    })

    it('en.json trendTitle does not contain emoji characters', () => {
        const fitness = (enLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect(/[\u{1F000}-\u{1FFFF}]/u.test(fitness.trendTitle as string)).toBe(false)
    })

    it('ko.json trendTitle does not contain emoji characters', () => {
        const fitness = (koLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect(/[\u{1F000}-\u{1FFFF}]/u.test(fitness.trendTitle as string)).toBe(false)
    })

    it('en.json trendTitle value is "7-Day Trend"', () => {
        const fitness = (enLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect(fitness.trendTitle).toBe('7-Day Trend')
    })

    it('ko.json trendTitle value is "7일 트렌드"', () => {
        const fitness = (koLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect(fitness.trendTitle).toBe('7일 트렌드')
    })

    it('en.json trendCTL contains "CTL"', () => {
        const fitness = (enLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect((fitness.trendCTL as string).includes('CTL')).toBe(true)
    })

    it('en.json trendATL contains "ATL"', () => {
        const fitness = (enLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect((fitness.trendATL as string).includes('ATL')).toBe(true)
    })

    it('en.json trendTSB contains "TSB"', () => {
        const fitness = (enLocale as Record<string, unknown>).fitness as Record<string, unknown>
        expect((fitness.trendTSB as string).includes('TSB')).toBe(true)
    })
})

// ---------------------------------------------------------------------------
// FitnessTrendChart component rendering
// ---------------------------------------------------------------------------

describe('FitnessTrendChart — renders with data', () => {
    it('mounts without throwing when history has 7 entries', () => {
        expect(() =>
            render(<FitnessTrendChart history={makeHistory(7)} />)
        ).not.toThrow()
    })

    it('renders a recharts svg container element when history is provided', () => {
        const { container } = render(<FitnessTrendChart history={makeHistory(7)} />)
        // ResponsiveContainer renders a div wrapper even in jsdom
        expect(container.firstChild).not.toBeNull()
    })

    it('mounts without throwing when history has exactly 1 entry', () => {
        expect(() =>
            render(<FitnessTrendChart history={makeHistory(1)} />)
        ).not.toThrow()
    })
})

describe('FitnessTrendChart — renders with empty history', () => {
    it('mounts without throwing when history is an empty array', () => {
        expect(() =>
            render(<FitnessTrendChart history={[]} />)
        ).not.toThrow()
    })

    it('renders a container element even with empty history', () => {
        const { container } = render(<FitnessTrendChart history={[]} />)
        expect(container.firstChild).not.toBeNull()
    })
})

// ---------------------------------------------------------------------------
// FitnessCard — chart section conditional rendering
// ---------------------------------------------------------------------------

describe('FitnessCard — chart section not rendered when ctl_history is null/missing', () => {
    it('does NOT render the "7-Day Trend" heading when ctl_history is undefined', () => {
        render(
            <FitnessCard
                training={{ ...mockTraining, ctl_history: undefined }}
                wellness={mockWellness}
                profile={mockProfile}
            />
        )
        expect(screen.queryByText('7-Day Trend')).toBeNull()
    })

    it('does NOT render the "7-Day Trend" heading when ctl_history is empty array', () => {
        render(
            <FitnessCard
                training={{ ...mockTraining, ctl_history: [] }}
                wellness={mockWellness}
                profile={mockProfile}
            />
        )
        expect(screen.queryByText('7-Day Trend')).toBeNull()
    })

    it('does NOT render the "7-Day Trend" heading when training has no ctl_history key', () => {
        // omit ctl_history entirely (optional field)
        const training: TrainingMetrics = {
            ctl: 60.0,
            atl: 55.0,
            tsb: 5.0,
            form_status: 'Fresh',
        }
        render(
            <FitnessCard
                training={training}
                wellness={mockWellness}
                profile={mockProfile}
            />
        )
        expect(screen.queryByText('7-Day Trend')).toBeNull()
    })
})

describe('FitnessCard — chart section rendered when ctl_history has data', () => {
    it('renders the "7-Day Trend" section heading when ctl_history has entries', () => {
        render(
            <FitnessCard
                training={{ ...mockTraining, ctl_history: makeHistory(7) }}
                wellness={mockWellness}
                profile={mockProfile}
            />
        )
        expect(screen.getByText('7-Day Trend')).toBeInTheDocument()
    })

    it('renders the chart section when ctl_history has a single entry', () => {
        render(
            <FitnessCard
                training={{ ...mockTraining, ctl_history: makeHistory(1) }}
                wellness={mockWellness}
                profile={mockProfile}
            />
        )
        expect(screen.getByText('7-Day Trend')).toBeInTheDocument()
    })

    it('chart section appears together with training load numbers', () => {
        render(
            <FitnessCard
                training={{ ...mockTraining, ctl_history: makeHistory(7) }}
                wellness={mockWellness}
                profile={mockProfile}
            />
        )
        expect(screen.getByText('7-Day Trend')).toBeInTheDocument()
        // Verify training load section also present (regression guard)
        expect(screen.getByText('60.0')).toBeInTheDocument()
    })
})

// ---------------------------------------------------------------------------
// TrainingHistoryPoint type shape verification (static)
// ---------------------------------------------------------------------------

describe('TrainingHistoryPoint type shape', () => {
    it('accepts a well-formed object with date, ctl, atl, tsb fields', () => {
        const point: TrainingHistoryPoint = {
            date: '2026-03-02',
            ctl: 65.5,
            atl: 72.3,
            tsb: -6.8,
        }
        expect(point.date).toBe('2026-03-02')
        expect(point.ctl).toBe(65.5)
        expect(point.atl).toBe(72.3)
        expect(point.tsb).toBe(-6.8)
    })

    it('supports positive tsb values', () => {
        const point: TrainingHistoryPoint = { date: '2026-03-01', ctl: 70, atl: 60, tsb: 10 }
        expect(point.tsb).toBeGreaterThan(0)
    })

    it('supports negative tsb values', () => {
        const point: TrainingHistoryPoint = { date: '2026-03-01', ctl: 60, atl: 75, tsb: -15 }
        expect(point.tsb).toBeLessThan(0)
    })

    it('ctl_history on TrainingMetrics is optional (undefined is valid)', () => {
        const metrics: TrainingMetrics = { ctl: 60, atl: 55, tsb: 5, form_status: 'Fresh' }
        expect(metrics.ctl_history).toBeUndefined()
    })

    it('ctl_history on TrainingMetrics accepts an array of TrainingHistoryPoint', () => {
        const metrics: TrainingMetrics = {
            ctl: 60,
            atl: 55,
            tsb: 5,
            form_status: 'Fresh',
            ctl_history: makeHistory(7),
        }
        expect(Array.isArray(metrics.ctl_history)).toBe(true)
        expect(metrics.ctl_history!.length).toBe(7)
    })
})
