/**
 * Tests for WeeklyTssProgressBar component
 *
 * Covers:
 * - tssProgress is null → renders null
 * - target is 0 → renders null
 * - isLoading → shows skeleton UI
 * - normal case: TSS values + percentage displayed
 * - 100%+ achieved case: celebration message shown
 * - warning case: unachievable warning rendered
 * - gradient classes: cyan-to-violet vs green
 * - mount animation: animatedWidth starts at 0
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { WeeklyTssProgressBar } from './WeeklyTssProgressBar'

// Base TssProgressData used across tests
const baseTssProgress = {
    target: 400,
    accumulated: 200,
    remaining: 200,
    daysRemaining: 4,
    achievable: true,
}

describe('WeeklyTssProgressBar', () => {
    beforeEach(() => {
        vi.useFakeTimers()
    })

    afterEach(() => {
        vi.useRealTimers()
    })

    // ------------------------------------------------------------------
    // Null / hidden cases
    // ------------------------------------------------------------------

    it('returns null when tssProgress is null and not loading', () => {
        const { container } = render(
            <WeeklyTssProgressBar tssProgress={null} isLoading={false} />
        )
        expect(container.firstChild).toBeNull()
    })

    it('returns null when target is 0 and not loading', () => {
        const { container } = render(
            <WeeklyTssProgressBar
                tssProgress={{ ...baseTssProgress, target: 0 }}
                isLoading={false}
            />
        )
        expect(container.firstChild).toBeNull()
    })

    it('returns null when target is negative and not loading', () => {
        const { container } = render(
            <WeeklyTssProgressBar
                tssProgress={{ ...baseTssProgress, target: -10 }}
                isLoading={false}
            />
        )
        expect(container.firstChild).toBeNull()
    })

    // ------------------------------------------------------------------
    // Loading skeleton
    // ------------------------------------------------------------------

    it('renders skeleton elements when isLoading is true', () => {
        const { container } = render(
            <WeeklyTssProgressBar tssProgress={null} isLoading={true} />
        )
        // Should render something (not null)
        expect(container.firstChild).not.toBeNull()
        // The skeleton div structure should be present
        // We look for the rounded-full skeleton bars
        const skeletonBars = container.querySelectorAll('.rounded-full')
        expect(skeletonBars.length).toBeGreaterThan(0)
    })

    it('renders skeleton even when tssProgress data is provided but isLoading is true', () => {
        const { container } = render(
            <WeeklyTssProgressBar tssProgress={baseTssProgress} isLoading={true} />
        )
        expect(container.firstChild).not.toBeNull()
        // Progress label text should NOT be visible during loading
        expect(screen.queryByText(/200\/400 TSS/)).toBeNull()
    })

    // ------------------------------------------------------------------
    // Normal case (50% progress)
    // ------------------------------------------------------------------

    it('shows TSS values as progress label (desktop card visible in DOM)', () => {
        render(
            <WeeklyTssProgressBar tssProgress={baseTssProgress} isLoading={false} />
        )
        // The label "200/400 TSS" should appear (from i18n: "{{accumulated}}/{{target}} TSS")
        // It appears in both mobile and desktop sections
        const progressLabels = screen.getAllByText('200/400 TSS')
        expect(progressLabels.length).toBeGreaterThan(0)
    })

    it('shows the percentage value', () => {
        render(
            <WeeklyTssProgressBar tssProgress={baseTssProgress} isLoading={false} />
        )
        // 200/400 = 50%
        const percentageElements = screen.getAllByText('50%')
        expect(percentageElements.length).toBeGreaterThan(0)
    })

    it('shows "Weekly Progress" label in desktop card', () => {
        render(
            <WeeklyTssProgressBar tssProgress={baseTssProgress} isLoading={false} />
        )
        // Desktop card shows "weeklyPlan.weeklyProgress" = "Weekly Progress"
        expect(screen.getByText('Weekly Progress')).toBeInTheDocument()
    })

    it('does NOT show celebration message when below 100%', () => {
        render(
            <WeeklyTssProgressBar tssProgress={baseTssProgress} isLoading={false} />
        )
        expect(screen.queryByText('Weekly TSS goal achieved!')).toBeNull()
        expect(screen.queryByText('TSS goal exceeded - great work!')).toBeNull()
    })

    it('uses cyan-to-violet gradient class when below 100%', () => {
        const { container } = render(
            <WeeklyTssProgressBar tssProgress={baseTssProgress} isLoading={false} />
        )
        const progressBars = container.querySelectorAll('.from-cyan-500')
        expect(progressBars.length).toBeGreaterThan(0)
    })

    // ------------------------------------------------------------------
    // 100% achieved case
    // ------------------------------------------------------------------

    it('shows goalAchieved celebration message when exactly 100%', () => {
        render(
            <WeeklyTssProgressBar
                tssProgress={{ ...baseTssProgress, accumulated: 400, remaining: 0 }}
                isLoading={false}
            />
        )
        // 400/400 = 100% → goalAchieved: "Weekly TSS goal achieved!"
        expect(screen.getAllByText('Weekly TSS goal achieved!').length).toBeGreaterThan(0)
    })

    it('shows goalExceeded celebration message when over 100%', () => {
        render(
            <WeeklyTssProgressBar
                tssProgress={{ ...baseTssProgress, accumulated: 500, remaining: 0 }}
                isLoading={false}
            />
        )
        // 500/400 = 125% → goalExceeded: "TSS goal exceeded - great work!"
        expect(screen.getAllByText('TSS goal exceeded - great work!').length).toBeGreaterThan(0)
    })

    it('uses green gradient class when achieved (>=100%)', () => {
        const { container } = render(
            <WeeklyTssProgressBar
                tssProgress={{ ...baseTssProgress, accumulated: 400, remaining: 0 }}
                isLoading={false}
            />
        )
        const greenBars = container.querySelectorAll('.from-green-400')
        expect(greenBars.length).toBeGreaterThan(0)
        // Cyan gradient should NOT be present
        const cyanBars = container.querySelectorAll('.from-cyan-500')
        expect(cyanBars.length).toBe(0)
    })

    it('caps the progress bar width at 100% even when accumulated > target', () => {
        const { container } = render(
            <WeeklyTssProgressBar
                tssProgress={{ ...baseTssProgress, accumulated: 600, remaining: 0 }}
                isLoading={false}
            />
        )
        // After animation timer fires (100ms), width should be capped at 100
        act(() => {
            vi.advanceTimersByTime(200)
        })
        const progressBarDivs = container.querySelectorAll('[style*="width"]')
        progressBarDivs.forEach((el) => {
            const widthVal = (el as HTMLElement).style.width
            if (widthVal) {
                const numVal = parseFloat(widthVal)
                expect(numVal).toBeLessThanOrEqual(100)
            }
        })
    })

    // ------------------------------------------------------------------
    // Mount animation
    // ------------------------------------------------------------------

    it('starts with animatedWidth 0 before timer fires', () => {
        const { container } = render(
            <WeeklyTssProgressBar tssProgress={baseTssProgress} isLoading={false} />
        )
        // Before any timer fires, width should be 0%
        const progressBarDivs = container.querySelectorAll('[style*="width"]')
        progressBarDivs.forEach((el) => {
            expect((el as HTMLElement).style.width).toBe('0%')
        })
    })

    it('animates width to actual value after 100ms timer', () => {
        const { container } = render(
            <WeeklyTssProgressBar tssProgress={baseTssProgress} isLoading={false} />
        )
        // 200/400 = 50%, capped at 50%
        act(() => {
            vi.advanceTimersByTime(150)
        })
        const progressBarDivs = container.querySelectorAll('[style*="width"]')
        const widths = Array.from(progressBarDivs).map(
            (el) => (el as HTMLElement).style.width
        )
        expect(widths.some((w) => w === '50%')).toBe(true)
    })

    // ------------------------------------------------------------------
    // Warning case (desktop only)
    // ------------------------------------------------------------------

    it('shows raw warning text when warning is a plain string', () => {
        render(
            <WeeklyTssProgressBar
                tssProgress={{
                    ...baseTssProgress,
                    achievable: false,
                    warning: 'Goal is unreachable',
                }}
                isLoading={false}
            />
        )
        expect(screen.getByText('Goal is unreachable')).toBeInTheDocument()
    })

    it('shows parsed warning with i18n key when warning is valid JSON', () => {
        const warningJson = JSON.stringify({
            days: 2,
            target: 400,
            accumulated: 50,
            pct: 12,
        })
        render(
            <WeeklyTssProgressBar
                tssProgress={{
                    ...baseTssProgress,
                    achievable: false,
                    warning: warningJson,
                }}
                isLoading={false}
            />
        )
        // The i18n key "tssWarningUnachievable" should produce a warning message
        // "Reaching TSS target 400 is unlikely with 2 days remaining. Currently 50/400 (12%). Adjust target?"
        const warningEl = screen.queryByText(/Reaching TSS target/)
        expect(warningEl).toBeInTheDocument()
    })

    it('does NOT show warning when isAchieved (>=100%)', () => {
        const warningJson = JSON.stringify({
            days: 2,
            target: 400,
            accumulated: 400,
            pct: 100,
        })
        render(
            <WeeklyTssProgressBar
                tssProgress={{
                    ...baseTssProgress,
                    accumulated: 400,
                    remaining: 0,
                    achievable: true,
                    warning: warningJson,
                }}
                isLoading={false}
            />
        )
        // Warning should not appear when isAchieved is true
        expect(screen.queryByText(/Reaching TSS target/)).toBeNull()
    })

    // ------------------------------------------------------------------
    // Percentage rounding
    // ------------------------------------------------------------------

    it('rounds percentage to nearest integer', () => {
        render(
            <WeeklyTssProgressBar
                tssProgress={{ ...baseTssProgress, accumulated: 133, target: 400 }}
                isLoading={false}
            />
        )
        // 133/400 = 33.25% → rounds to 33%
        const percentageElements = screen.getAllByText('33%')
        expect(percentageElements.length).toBeGreaterThan(0)
    })

    // ------------------------------------------------------------------
    // isLoading with data present
    // ------------------------------------------------------------------

    it('shows skeleton loading state and hides real content when isLoading=true with real data', () => {
        render(
            <WeeklyTssProgressBar tssProgress={baseTssProgress} isLoading={true} />
        )
        // Real percentage text should not be visible
        expect(screen.queryByText('50%')).toBeNull()
        // Weekly Progress label from desktop card should not be visible
        expect(screen.queryByText('Weekly Progress')).toBeNull()
    })
})
