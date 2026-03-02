/**
 * Tests for WeeklyCalendarCard component — Compact row layout (task #219)
 *
 * Covers:
 * - i18n keys: dayNamesFull, restDay, planLabel, doneLabel exist in both locales
 * - Compact row layout: day name + badge + workout name + TSS inline
 * - Rest day rows
 * - Plan/Done badge elements
 * - Event name truncation
 * - Event style (planned vs actual)
 * - onSelectDate callback
 * - Legend footer
 * - Loading / null states
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { WeeklyCalendarCard } from './WeeklyCalendarCard'
import type { WeeklyCalendarData } from '@/lib/api'
import enLocale from '../i18n/locales/en.json'
import koLocale from '../i18n/locales/ko.json'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Monday of the week containing 2026-02-16 (a known Monday) */
const WEEK_START = '2026-02-16'

function makeCalendar(overrides: Partial<WeeklyCalendarData> = {}): WeeklyCalendarData {
    return {
        week_start: WEEK_START,
        week_end: '2026-02-22',
        events: [],
        planned_tss: 0,
        actual_tss: 0,
        ...overrides,
    }
}

const plannedEvent = {
    id: 'evt-plan-1',
    date: WEEK_START, // Monday
    name: 'Threshold Intervals',
    category: 'Ride',
    workout_type: 'Ride',
    duration_minutes: 60,
    tss: 80,
    description: null,
    is_actual: false,
}

const actualEvent = {
    id: 'evt-actual-1',
    date: WEEK_START,
    name: 'Morning Ride',
    category: 'Ride',
    workout_type: 'Ride',
    duration_minutes: 45,
    tss: 55,
    description: null,
    is_actual: true,
}

// ---------------------------------------------------------------------------
// i18n locale key tests (static JSON inspection)
// ---------------------------------------------------------------------------

describe('i18n locale files — new calendar keys', () => {
    it('en.json has calendar.dayNamesFull as an array of 7 entries', () => {
        const dayNamesFull = (enLocale as Record<string, unknown>).calendar as Record<string, unknown>
        expect(Array.isArray(dayNamesFull.dayNamesFull)).toBe(true)
        expect((dayNamesFull.dayNamesFull as string[]).length).toBe(7)
    })

    it('en.json has calendar.restDay string', () => {
        const calendar = (enLocale as Record<string, unknown>).calendar as Record<string, unknown>
        expect(typeof calendar.restDay).toBe('string')
        expect((calendar.restDay as string).length).toBeGreaterThan(0)
    })

    it('en.json has calendar.planLabel string', () => {
        const calendar = (enLocale as Record<string, unknown>).calendar as Record<string, unknown>
        expect(typeof calendar.planLabel).toBe('string')
        expect((calendar.planLabel as string).length).toBeGreaterThan(0)
    })

    it('en.json has calendar.doneLabel string', () => {
        const calendar = (enLocale as Record<string, unknown>).calendar as Record<string, unknown>
        expect(typeof calendar.doneLabel).toBe('string')
        expect((calendar.doneLabel as string).length).toBeGreaterThan(0)
    })

    it('ko.json has calendar.dayNamesFull as an array of 7 entries', () => {
        const calendar = (koLocale as Record<string, unknown>).calendar as Record<string, unknown>
        expect(Array.isArray(calendar.dayNamesFull)).toBe(true)
        expect((calendar.dayNamesFull as string[]).length).toBe(7)
    })

    it('ko.json has calendar.restDay string', () => {
        const calendar = (koLocale as Record<string, unknown>).calendar as Record<string, unknown>
        expect(typeof calendar.restDay).toBe('string')
        expect((calendar.restDay as string).length).toBeGreaterThan(0)
    })

    it('ko.json has calendar.planLabel string', () => {
        const calendar = (koLocale as Record<string, unknown>).calendar as Record<string, unknown>
        expect(typeof calendar.planLabel).toBe('string')
        expect((calendar.planLabel as string).length).toBeGreaterThan(0)
    })

    it('ko.json has calendar.doneLabel string', () => {
        const calendar = (koLocale as Record<string, unknown>).calendar as Record<string, unknown>
        expect(typeof calendar.doneLabel).toBe('string')
        expect((calendar.doneLabel as string).length).toBeGreaterThan(0)
    })

    it('en.json dayNamesFull does not contain emoji characters', () => {
        const calendar = (enLocale as Record<string, unknown>).calendar as Record<string, unknown>
        const names = calendar.dayNamesFull as string[]
        // No emoji — each full day name should be plain text only
        names.forEach(name => {
            expect(/[\u{1F000}-\u{1FFFF}]/u.test(name)).toBe(false)
        })
    })

    it('ko.json restDay does not contain emoji characters', () => {
        const calendar = (koLocale as Record<string, unknown>).calendar as Record<string, unknown>
        expect(/[\u{1F000}-\u{1FFFF}]/u.test(calendar.restDay as string)).toBe(false)
    })
})

// ---------------------------------------------------------------------------
// Component render tests
// ---------------------------------------------------------------------------

describe('WeeklyCalendarCard', () => {
    // -----------------------------------------------------------------------
    // Null / loading cases
    // -----------------------------------------------------------------------

    it('renders null when calendar is null and not loading', () => {
        const { container } = render(
            <WeeklyCalendarCard calendar={null} isLoading={false} />
        )
        expect(container.firstChild).toBeNull()
    })

    it('renders skeleton when isLoading is true', () => {
        const { container } = render(
            <WeeklyCalendarCard calendar={null} isLoading={true} />
        )
        expect(container.firstChild).not.toBeNull()
        // Loading title should still be present
        expect(screen.getByText('This Week\'s Overview')).toBeInTheDocument()
        // Skeleton pulse div present
        const pulse = container.querySelector('.animate-pulse')
        expect(pulse).not.toBeNull()
    })

    // -----------------------------------------------------------------------
    // Compact row container layout
    // -----------------------------------------------------------------------

    it('renders container with flex flex-col divide-y layout', () => {
        const { container } = render(
            <WeeklyCalendarCard calendar={makeCalendar()} isLoading={false} />
        )
        const rowContainer = container.querySelector('.flex.flex-col.divide-y')
        expect(rowContainer).not.toBeNull()
    })

    it('renders 7 rows when all days are rest days (one row per day)', () => {
        const { container } = render(
            <WeeklyCalendarCard calendar={makeCalendar()} isLoading={false} />
        )
        // Each day has exactly one row (rest day)
        const rows = container.querySelectorAll('.flex.items-center.gap-2.py-1\\.5.px-1')
        expect(rows.length).toBe(7)
    })

    it('renders 8 rows when one day has 2 events and rest are rest days', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [plannedEvent, actualEvent] })}
                isLoading={false}
            />
        )
        // Monday has 2 events (2 rows), other 6 days have 1 row each = 8 total
        const rows = container.querySelectorAll('.flex.items-center.gap-2.py-1\\.5.px-1')
        expect(rows.length).toBe(8)
    })

    // -----------------------------------------------------------------------
    // Day name column (w-24)
    // -----------------------------------------------------------------------

    it('renders day name spans with w-24 fixed width for all 7 days', () => {
        const { container } = render(
            <WeeklyCalendarCard calendar={makeCalendar()} isLoading={false} />
        )
        const dayNameSpans = container.querySelectorAll('.w-24.shrink-0')
        expect(dayNameSpans.length).toBe(7)
    })

    it('shows full day name "Monday" in the day name column for the first day', () => {
        render(<WeeklyCalendarCard calendar={makeCalendar()} isLoading={false} />)
        expect(screen.getByText(/Monday/)).toBeInTheDocument()
    })

    it('makes second row day name invisible when a day has multiple events', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [plannedEvent, actualEvent] })}
                isLoading={false}
            />
        )
        const invisibleDayNames = container.querySelectorAll('.w-24.shrink-0.invisible')
        // Monday has 2 events, so 2nd row day name should be invisible
        expect(invisibleDayNames.length).toBe(1)
    })

    // -----------------------------------------------------------------------
    // Rest day display
    // -----------------------------------------------------------------------

    it('shows rest day text element in the DOM when a day has no events', () => {
        // Calendar with no events — all 7 days are rest days
        render(
            <WeeklyCalendarCard calendar={makeCalendar()} isLoading={false} />
        )
        const restDayTexts = screen.getAllByText('Rest Day')
        expect(restDayTexts.length).toBe(7)
    })

    it('shows the rest day i18n text "Rest Day" when a day has no events', () => {
        render(<WeeklyCalendarCard calendar={makeCalendar()} isLoading={false} />)
        const restDayTexts = screen.getAllByText('Rest Day')
        expect(restDayTexts.length).toBe(7)
    })

    it('does not show rest day text when a day has events', () => {
        render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [plannedEvent] })}
                isLoading={false}
            />
        )
        // Monday has an event, so only 6 days should show rest day text
        const restDayTexts = screen.getAllByText('Rest Day')
        expect(restDayTexts.length).toBe(6)
    })

    // -----------------------------------------------------------------------
    // Plan / Done badges
    // -----------------------------------------------------------------------

    it('renders plan badge element for a planned event', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [plannedEvent] })}
                isLoading={false}
            />
        )
        const planBadges = container.querySelectorAll('.inline-flex.bg-blue-200')
        expect(planBadges.length).toBeGreaterThan(0)
    })

    it('renders done badge element for an actual/completed event', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [actualEvent] })}
                isLoading={false}
            />
        )
        const doneBadges = container.querySelectorAll('.inline-flex.bg-green-200')
        expect(doneBadges.length).toBeGreaterThan(0)
    })

    it('plan badge text reads the planLabel i18n key ("Plan")', () => {
        render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [plannedEvent] })}
                isLoading={false}
            />
        )
        expect(screen.getByText('Plan')).toBeInTheDocument()
    })

    it('done badge text reads the doneLabel i18n key ("Done")', () => {
        render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [actualEvent] })}
                isLoading={false}
            />
        )
        expect(screen.getByText('Done')).toBeInTheDocument()
    })

    it('plan badge has blue-200 background class', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [plannedEvent] })}
                isLoading={false}
            />
        )
        const planBadge = container.querySelector('.bg-blue-200')
        expect(planBadge).not.toBeNull()
    })

    it('done badge has green-200 background class', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [actualEvent] })}
                isLoading={false}
            />
        )
        const doneBadge = container.querySelector('.bg-green-200')
        expect(doneBadge).not.toBeNull()
    })

    // -----------------------------------------------------------------------
    // Event name truncation
    // -----------------------------------------------------------------------

    it('event name span has truncate class for compact row layout', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [plannedEvent] })}
                isLoading={false}
            />
        )
        const truncateSpans = container.querySelectorAll('.truncate')
        expect(truncateSpans.length).toBeGreaterThan(0)
    })

    it('event wrapper div uses min-w-0 flex-1 for truncation to work', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [plannedEvent] })}
                isLoading={false}
            />
        )
        const eventDivs = container.querySelectorAll('.min-w-0.flex-1')
        expect(eventDivs.length).toBeGreaterThan(0)
    })

    // -----------------------------------------------------------------------
    // TSS display
    // -----------------------------------------------------------------------

    it('shows TSS value for an event that has tss set', () => {
        render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [plannedEvent] })}
                isLoading={false}
            />
        )
        // plannedEvent.tss = 80 → should render "TSS 80"
        expect(screen.getByText(/TSS 80/)).toBeInTheDocument()
    })

    it('shows duration inline with TSS', () => {
        render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [plannedEvent] })}
                isLoading={false}
            />
        )
        // plannedEvent: tss=80, duration_minutes=60 → "TSS 80 · 60m"
        expect(screen.getByText(/TSS 80 · 60m/)).toBeInTheDocument()
    })

    // -----------------------------------------------------------------------
    // Event style — planned vs actual
    // -----------------------------------------------------------------------

    it('planned event wrapper has blue dashed border style', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [plannedEvent] })}
                isLoading={false}
            />
        )
        const eventDivs = container.querySelectorAll('[style*="dashed"]')
        expect(eventDivs.length).toBeGreaterThan(0)
    })

    it('actual event wrapper has solid green border style', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [actualEvent] })}
                isLoading={false}
            />
        )
        const eventDivs = container.querySelectorAll('[style*="solid"]')
        expect(eventDivs.length).toBeGreaterThan(0)
    })

    // -----------------------------------------------------------------------
    // onSelectDate callback
    // -----------------------------------------------------------------------

    it('calls onSelectDate with the day date string when a row is clicked', async () => {
        const { userEvent } = await import('@testing-library/user-event')
        const onSelectDate = vi.fn()
        const user = userEvent.setup()

        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar()}
                isLoading={false}
                onSelectDate={onSelectDate}
            />
        )

        // Click the first row (Monday = WEEK_START)
        const rows = container.querySelectorAll('.cursor-pointer')
        await user.click(rows[0])
        expect(onSelectDate).toHaveBeenCalledWith(WEEK_START)
    })

    // -----------------------------------------------------------------------
    // Legend footer
    // -----------------------------------------------------------------------

    it('renders legend section with completedLegend and plannedLegend i18n strings', () => {
        render(<WeeklyCalendarCard calendar={makeCalendar()} isLoading={false} />)
        expect(screen.getByText('Completed activities')).toBeInTheDocument()
        expect(screen.getByText('Planned workouts')).toBeInTheDocument()
    })
})
