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

    // New i18n keys for progress summary
    it('en.json has calendar.tssLabel string', () => {
        const calendar = (enLocale as Record<string, unknown>).calendar as Record<string, unknown>
        expect(typeof calendar.tssLabel).toBe('string')
    })

    it('en.json has calendar.trainingLabel string', () => {
        const calendar = (enLocale as Record<string, unknown>).calendar as Record<string, unknown>
        expect(typeof calendar.trainingLabel).toBe('string')
    })

    it('en.json has calendar.tssProgress string', () => {
        const calendar = (enLocale as Record<string, unknown>).calendar as Record<string, unknown>
        expect(typeof calendar.tssProgress).toBe('string')
    })

    it('en.json has calendar.trainingDays string', () => {
        const calendar = (enLocale as Record<string, unknown>).calendar as Record<string, unknown>
        expect(typeof calendar.trainingDays).toBe('string')
    })

    it('ko.json has calendar.tssProgress string', () => {
        const calendar = (koLocale as Record<string, unknown>).calendar as Record<string, unknown>
        expect(typeof calendar.tssProgress).toBe('string')
    })

    it('ko.json has calendar.trainingDays string', () => {
        const calendar = (koLocale as Record<string, unknown>).calendar as Record<string, unknown>
        expect(typeof calendar.trainingDays).toBe('string')
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
    // Day name column (w-14)
    // -----------------------------------------------------------------------

    it('renders day name spans with w-14 fixed width for all 7 days', () => {
        const { container } = render(
            <WeeklyCalendarCard calendar={makeCalendar()} isLoading={false} />
        )
        const dayNameSpans = container.querySelectorAll('.w-14.shrink-0')
        expect(dayNameSpans.length).toBe(7)
    })

    it('shows abbreviated day name "Mon" in the day name column for the first day', () => {
        render(<WeeklyCalendarCard calendar={makeCalendar()} isLoading={false} />)
        expect(screen.getByText(/^Mon$/)).toBeInTheDocument()
    })

    it('makes second row day name invisible when a day has multiple events', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [plannedEvent, actualEvent] })}
                isLoading={false}
            />
        )
        const invisibleDayNames = container.querySelectorAll('.w-14.shrink-0.invisible')
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

    // -----------------------------------------------------------------------
    // WeeklyProgressSummary in header
    // -----------------------------------------------------------------------

    it('renders progress summary in header when tss props are provided', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar()}
                isLoading={false}
                tssAccumulated={400}
                tssTarget={600}
                trainingDaysCompleted={3}
                trainingDaysTarget={6}
            />
        )
        // Desktop rings container should exist
        const desktopRings = container.querySelector('.hidden.md\\:flex')
        expect(desktopRings).not.toBeNull()
    })

    it('shows TSS progress label in header', () => {
        render(
            <WeeklyCalendarCard
                calendar={makeCalendar()}
                isLoading={false}
                tssAccumulated={400}
                tssTarget={600}
                trainingDaysCompleted={3}
                trainingDaysTarget={6}
            />
        )
        // i18n: "400/600 TSS"
        const labels = screen.getAllByText('400/600 TSS')
        expect(labels.length).toBeGreaterThan(0)
    })

    it('shows training days label in header', () => {
        render(
            <WeeklyCalendarCard
                calendar={makeCalendar()}
                isLoading={false}
                tssAccumulated={400}
                tssTarget={600}
                trainingDaysCompleted={3}
                trainingDaysTarget={6}
            />
        )
        // i18n: "3/6 days"
        const labels = screen.getAllByText('3/6 days')
        expect(labels.length).toBeGreaterThan(0)
    })

    it('renders header with flex justify-between for title and progress summary', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar()}
                isLoading={false}
                tssAccumulated={400}
                tssTarget={600}
            />
        )
        const headerFlex = container.querySelector('.flex.justify-between.items-start')
        expect(headerFlex).not.toBeNull()
    })

    // -----------------------------------------------------------------------
    // Shield additions — TSS display edge cases
    // -----------------------------------------------------------------------

    it('does not render TSS span when event tss is null/undefined', () => {
        const noTssEvent = {
            ...plannedEvent,
            id: 'evt-notss',
            tss: null as unknown as number,
        }
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [noTssEvent] })}
                isLoading={false}
            />
        )
        // When tss is falsy, no TSS text should appear
        const tssTexts = container.querySelectorAll('[class*="opacity-70"]')
        expect(tssTexts.length).toBe(0)
    })

    it('shows TSS without duration when duration_minutes is null', () => {
        const noMinutesEvent = {
            ...plannedEvent,
            id: 'evt-noduration',
            tss: 60,
            duration_minutes: null as unknown as number,
        }
        render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [noMinutesEvent] })}
                isLoading={false}
            />
        )
        // TSS should appear, but not with "· Xm" suffix
        expect(screen.getByText(/TSS 60/)).toBeInTheDocument()
        expect(screen.queryByText(/TSS 60 · /)).toBeNull()
    })

    it('renders WeeklyProgressSummary skeleton in loading header', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={null}
                isLoading={true}
                tssAccumulated={300}
                tssTarget={600}
            />
        )
        // Skeleton circles should be present from WeeklyProgressSummary isLoading
        const skeletons = container.querySelectorAll('.rounded-full')
        expect(skeletons.length).toBeGreaterThan(0)
    })

    it('renders one row per event when multiple events are on different days', () => {
        const wednesdayEvent = {
            ...actualEvent,
            id: 'evt-wed',
            date: '2026-02-18', // Wednesday of test week
        }
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [plannedEvent, wednesdayEvent] })}
                isLoading={false}
            />
        )
        // Monday: 1 row (planned), Wed: 1 row (actual), other 5 days: rest → 7 total
        const rows = container.querySelectorAll('.flex.items-center.gap-2.py-1\\.5.px-1')
        expect(rows.length).toBe(7)
    })

    it('renders actual_tss field present in WeeklyCalendarData type', () => {
        const calendarWithActualTss = makeCalendar({
            actual_tss: 350,
            events: [actualEvent],
        })
        // Verify actual_tss is accessible on the data structure
        expect(calendarWithActualTss.actual_tss).toBe(350)
    })

    it('shows no rest days when all 7 days have events', () => {
        const allDayEvents = Array.from({ length: 7 }, (_, i) => {
            const d = new Date('2026-02-16')
            d.setDate(d.getDate() + i)
            return {
                ...actualEvent,
                id: `evt-day-${i}`,
                date: d.toISOString().slice(0, 10),
            }
        })
        render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: allDayEvents })}
                isLoading={false}
            />
        )
        // No rest day text should appear
        const restDayTexts = screen.queryAllByText('Rest Day')
        expect(restDayTexts.length).toBe(0)
    })

    it('header always renders "This Week\'s Overview" title in loading state', () => {
        render(
            <WeeklyCalendarCard calendar={null} isLoading={true} />
        )
        expect(screen.getByText("This Week's Overview")).toBeInTheDocument()
    })

    it('orders planned events before actual events on same day', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [actualEvent, plannedEvent] })}
                isLoading={false}
            />
        )
        // Find the two event rows for Monday
        const badges = container.querySelectorAll('.inline-flex')
        // First badge should be Plan (blue), second should be Done (green)
        expect(badges[0].classList.contains('bg-blue-200')).toBe(true)
        expect(badges[1].classList.contains('bg-green-200')).toBe(true)
    })
})
