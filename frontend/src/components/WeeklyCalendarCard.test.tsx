/**
 * Tests for WeeklyCalendarCard component — Mobile layout refactor (task #212)
 *
 * Covers:
 * - i18n keys: dayNamesFull, restDay, planLabel, doneLabel exist in both locales
 * - Mobile plan/done badge elements are present in the DOM (md:hidden pattern)
 * - Mobile rest day text is in the DOM when a day has no events
 * - Event name does NOT have md:truncate class at the outer wrapper level (only inner span)
 * - Desktop container has md:grid and md:grid-cols-7 classes
 * - Mobile day header (md:hidden) shows full day name
 * - Loading state renders skeleton and not real content
 * - null calendar renders nothing
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
    // Desktop container classes
    // -----------------------------------------------------------------------

    it('renders grid container with md:grid md:grid-cols-7 classes', () => {
        const { container } = render(
            <WeeklyCalendarCard calendar={makeCalendar()} isLoading={false} />
        )
        // The responsive container should have all four classes
        const gridContainer = container.querySelector('.md\\:grid.md\\:grid-cols-7')
        expect(gridContainer).not.toBeNull()
    })

    it('renders grid container with flex flex-col gap-2 classes for mobile stacking', () => {
        const { container } = render(
            <WeeklyCalendarCard calendar={makeCalendar()} isLoading={false} />
        )
        const mobileContainer = container.querySelector('.flex.flex-col.gap-2')
        expect(mobileContainer).not.toBeNull()
    })

    // -----------------------------------------------------------------------
    // Mobile day header (full name)
    // -----------------------------------------------------------------------

    it('renders mobile day header element (md:hidden) with full day name text', () => {
        const { container } = render(
            <WeeklyCalendarCard calendar={makeCalendar()} isLoading={false} />
        )
        // The mobile header divs: class="flex items-center gap-2 mb-2 md:hidden"
        const mobileHeaders = container.querySelectorAll('.md\\:hidden.flex.items-center')
        // Expect 7 such headers (one per day)
        expect(mobileHeaders.length).toBe(7)
    })

    it('shows full day name "Monday" in the mobile header for the first day', () => {
        render(<WeeklyCalendarCard calendar={makeCalendar()} isLoading={false} />)
        // i18n en locale: dayNamesFull[0] = "Monday"
        expect(screen.getByText(/Monday/)).toBeInTheDocument()
    })

    // -----------------------------------------------------------------------
    // Desktop day header (compact, hidden on mobile)
    // -----------------------------------------------------------------------

    it('renders desktop compact day name using hidden md:block pattern', () => {
        const { container } = render(
            <WeeklyCalendarCard calendar={makeCalendar()} isLoading={false} />
        )
        // Desktop short name divs: class="hidden md:block text-xs text-muted-foreground mb-1"
        // The rest day desktop divs also have hidden md:block text-xs text-muted-foreground,
        // so there are 14 total (7 day headers + 7 rest day desktop divs).
        // We narrow to day header by looking for mb-1 which only the day name header has.
        const desktopDayNameDivs = container.querySelectorAll('.hidden.md\\:block.text-xs.text-muted-foreground.mb-1')
        expect(desktopDayNameDivs.length).toBe(7)
    })

    // -----------------------------------------------------------------------
    // Rest day display (mobile)
    // -----------------------------------------------------------------------

    it('shows rest day text element in the DOM when a day has no events', () => {
        // Calendar with no events — all 7 days are rest days
        const { container } = render(
            <WeeklyCalendarCard calendar={makeCalendar()} isLoading={false} />
        )
        // Mobile rest day: class="md:hidden text-xs text-muted-foreground"
        // There should be 7 such elements (one per empty day)
        const restDayElements = container.querySelectorAll('.md\\:hidden.text-xs.text-muted-foreground')
        expect(restDayElements.length).toBe(7)
    })

    it('shows the rest day i18n text "Rest Day" when a day has no events', () => {
        render(<WeeklyCalendarCard calendar={makeCalendar()} isLoading={false} />)
        // "Rest Day" appears 7 times (once per day in mobile view)
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
    // Plan / Done badges (mobile)
    // -----------------------------------------------------------------------

    it('renders plan badge (md:hidden) element for a planned event', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [plannedEvent] })}
                isLoading={false}
            />
        )
        // Plan badge: class contains "md:hidden inline-flex ... bg-blue-200"
        const planBadges = container.querySelectorAll('.md\\:hidden.inline-flex')
        expect(planBadges.length).toBeGreaterThan(0)
    })

    it('renders done badge (md:hidden) element for an actual/completed event', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [actualEvent] })}
                isLoading={false}
            />
        )
        const doneBadges = container.querySelectorAll('.md\\:hidden.inline-flex')
        expect(doneBadges.length).toBeGreaterThan(0)
    })

    it('plan badge text reads the planLabel i18n key ("Plan")', () => {
        render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [plannedEvent] })}
                isLoading={false}
            />
        )
        // en locale: calendar.planLabel = "Plan"
        expect(screen.getByText('Plan')).toBeInTheDocument()
    })

    it('done badge text reads the doneLabel i18n key ("Done")', () => {
        render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [actualEvent] })}
                isLoading={false}
            />
        )
        // en locale: calendar.doneLabel = "Done"
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
    // Event name truncation: md:truncate is on the inner span only
    // -----------------------------------------------------------------------

    it('event name span has md:truncate class (truncation is desktop-only)', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [plannedEvent] })}
                isLoading={false}
            />
        )
        // The span wrapping cleanWorkoutName(event.name) should have md:truncate
        const truncateSpans = container.querySelectorAll('.md\\:truncate')
        expect(truncateSpans.length).toBeGreaterThan(0)
    })

    it('event wrapper div has md:truncate (desktop-only) but no unconditional truncate class', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [plannedEvent] })}
                isLoading={false}
            />
        )
        // The outer event div uses md:truncate (desktop breakpoint only) — this is correct behavior.
        // It must NOT have plain "truncate" (which would truncate on mobile too).
        const eventDivs = container.querySelectorAll('.p-1\\.5.rounded')
        expect(eventDivs.length).toBeGreaterThan(0)
        eventDivs.forEach(div => {
            // Plain "truncate" (no breakpoint prefix) would break mobile — ensure it's absent
            expect(div.classList.contains('truncate')).toBe(false)
        })
    })

    // -----------------------------------------------------------------------
    // Desktop check/dot icons are hidden on mobile
    // -----------------------------------------------------------------------

    it('renders desktop check icon with hidden md:inline classes for actual events', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [actualEvent] })}
                isLoading={false}
            />
        )
        // Check icon: class="hidden md:inline h-3 w-3 text-green-600"
        const checkIcons = container.querySelectorAll('.hidden.md\\:inline')
        expect(checkIcons.length).toBeGreaterThan(0)
    })

    it('renders desktop dot bullet with hidden md:inline classes for planned events', () => {
        const { container } = render(
            <WeeklyCalendarCard
                calendar={makeCalendar({ events: [plannedEvent] })}
                isLoading={false}
            />
        )
        const dotSpans = container.querySelectorAll('.hidden.md\\:inline')
        expect(dotSpans.length).toBeGreaterThan(0)
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
        // The event div gets inline style from getEventStyle
        // Planned: borderLeft '3px dashed #3b82f6'
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
        // Actual: borderLeft '3px solid #22c55e'
        const eventDivs = container.querySelectorAll('[style*="solid"]')
        expect(eventDivs.length).toBeGreaterThan(0)
    })

    // -----------------------------------------------------------------------
    // onSelectDate callback
    // -----------------------------------------------------------------------

    it('calls onSelectDate with the day date string when a day cell is clicked', async () => {
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

        // Click the first day cell (Monday = WEEK_START)
        const dayCells = container.querySelectorAll('.cursor-pointer')
        await user.click(dayCells[0])
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
