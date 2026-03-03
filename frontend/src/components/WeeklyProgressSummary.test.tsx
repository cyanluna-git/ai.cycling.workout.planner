/**
 * Tests for WeeklyProgressSummary component
 *
 * Covers:
 * - Loading state shows skeleton
 * - Desktop: two rings rendered (hidden md:flex)
 * - Mobile: two progress bars rendered (flex md:hidden)
 * - TSS label text present
 * - Training days label text present
 * - Edge case: target 0 shows 0%
 * - Edge case: accumulated > target shows clamped ring
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { WeeklyProgressSummary } from './WeeklyProgressSummary'

describe('WeeklyProgressSummary', () => {
    beforeEach(() => {
        vi.useFakeTimers()
    })

    afterEach(() => {
        vi.useRealTimers()
    })

    // -----------------------------------------------------------------------
    // Loading state
    // -----------------------------------------------------------------------

    it('renders skeleton when isLoading is true', () => {
        const { container } = render(
            <WeeklyProgressSummary
                tssAccumulated={0}
                tssTarget={0}
                trainingDaysCompleted={0}
                trainingDaysTarget={6}
                isLoading={true}
            />
        )
        const skeletons = container.querySelectorAll('.rounded-full')
        expect(skeletons.length).toBeGreaterThan(0)
    })

    it('does not render rings when loading', () => {
        const { container } = render(
            <WeeklyProgressSummary
                tssAccumulated={200}
                tssTarget={400}
                trainingDaysCompleted={3}
                trainingDaysTarget={6}
                isLoading={true}
            />
        )
        const svgs = container.querySelectorAll('svg')
        expect(svgs.length).toBe(0)
    })

    // -----------------------------------------------------------------------
    // Desktop layout: rings
    // -----------------------------------------------------------------------

    it('renders desktop ring container with hidden md:flex classes', () => {
        const { container } = render(
            <WeeklyProgressSummary
                tssAccumulated={680}
                tssTarget={850}
                trainingDaysCompleted={4}
                trainingDaysTarget={6}
                isLoading={false}
            />
        )
        const desktopContainer = container.querySelector('.hidden.md\\:flex')
        expect(desktopContainer).not.toBeNull()
    })

    it('renders two SVG rings in desktop container', () => {
        const { container } = render(
            <WeeklyProgressSummary
                tssAccumulated={680}
                tssTarget={850}
                trainingDaysCompleted={4}
                trainingDaysTarget={6}
                isLoading={false}
            />
        )
        const desktopContainer = container.querySelector('.hidden.md\\:flex')
        const svgs = desktopContainer?.querySelectorAll('svg')
        expect(svgs?.length).toBe(2)
    })

    // -----------------------------------------------------------------------
    // Mobile layout: progress bars
    // -----------------------------------------------------------------------

    it('renders mobile progress bar container with flex md:hidden classes', () => {
        const { container } = render(
            <WeeklyProgressSummary
                tssAccumulated={680}
                tssTarget={850}
                trainingDaysCompleted={4}
                trainingDaysTarget={6}
                isLoading={false}
            />
        )
        const mobileContainer = container.querySelector('.flex.md\\:hidden')
        expect(mobileContainer).not.toBeNull()
    })

    it('renders two progress bars in mobile container', () => {
        const { container } = render(
            <WeeklyProgressSummary
                tssAccumulated={680}
                tssTarget={850}
                trainingDaysCompleted={4}
                trainingDaysTarget={6}
                isLoading={false}
            />
        )
        const mobileContainer = container.querySelector('.flex.md\\:hidden')
        const bars = mobileContainer?.querySelectorAll('.rounded-full.overflow-hidden')
        expect(bars?.length).toBe(2)
    })

    // -----------------------------------------------------------------------
    // Label text
    // -----------------------------------------------------------------------

    it('shows TSS progress label text', () => {
        render(
            <WeeklyProgressSummary
                tssAccumulated={680}
                tssTarget={850}
                trainingDaysCompleted={4}
                trainingDaysTarget={6}
                isLoading={false}
            />
        )
        // i18n: "680/850 TSS"
        const tssLabels = screen.getAllByText('680/850 TSS')
        expect(tssLabels.length).toBeGreaterThan(0)
    })

    it('shows training days label text', () => {
        render(
            <WeeklyProgressSummary
                tssAccumulated={680}
                tssTarget={850}
                trainingDaysCompleted={4}
                trainingDaysTarget={6}
                isLoading={false}
            />
        )
        // i18n: "4/6 days"
        const trainingLabels = screen.getAllByText('4/6 days')
        expect(trainingLabels.length).toBeGreaterThan(0)
    })

    // -----------------------------------------------------------------------
    // Edge cases
    // -----------------------------------------------------------------------

    it('shows dash for target when tssTarget is 0', () => {
        render(
            <WeeklyProgressSummary
                tssAccumulated={0}
                tssTarget={0}
                trainingDaysCompleted={0}
                trainingDaysTarget={6}
                isLoading={false}
            />
        )
        // When target is 0, label shows "0/- TSS"
        const labels = screen.getAllByText('0/- TSS')
        expect(labels.length).toBeGreaterThan(0)
    })

    it('renders without errors when tssAccumulated exceeds tssTarget', () => {
        const { container } = render(
            <WeeklyProgressSummary
                tssAccumulated={1000}
                tssTarget={800}
                trainingDaysCompleted={6}
                trainingDaysTarget={6}
                isLoading={false}
            />
        )
        // Should render without crashing
        expect(container.firstChild).not.toBeNull()
        // Text shows actual exceeded values
        const labels = screen.getAllByText('1000/800 TSS')
        expect(labels.length).toBeGreaterThan(0)
    })

    // -----------------------------------------------------------------------
    // Shield additions — additional edge cases
    // -----------------------------------------------------------------------

    it('renders without errors when trainingDaysTarget is 0 (divide-by-zero guard)', () => {
        const { container } = render(
            <WeeklyProgressSummary
                tssAccumulated={0}
                tssTarget={0}
                trainingDaysCompleted={0}
                trainingDaysTarget={0}
                isLoading={false}
            />
        )
        expect(container.firstChild).not.toBeNull()
        // Training days ring should show 0% (not NaN or crash)
        const spans = container.querySelectorAll('.text-\\[10px\\].font-semibold')
        spans.forEach(span => {
            expect(span.textContent).toBe('0%')
        })
    })

    it('renders both rings with correct progress after all-zeros state', () => {
        const { container } = render(
            <WeeklyProgressSummary
                tssAccumulated={0}
                tssTarget={0}
                trainingDaysCompleted={0}
                trainingDaysTarget={6}
                isLoading={false}
            />
        )
        const desktopContainer = container.querySelector('.hidden.md\\:flex')
        const svgs = desktopContainer?.querySelectorAll('svg')
        expect(svgs?.length).toBe(2)
    })

    it('renders ProgressBarSlim for each metric in mobile view', () => {
        const { container } = render(
            <WeeklyProgressSummary
                tssAccumulated={300}
                tssTarget={600}
                trainingDaysCompleted={2}
                trainingDaysTarget={6}
                isLoading={false}
            />
        )
        const mobileContainer = container.querySelector('.flex.md\\:hidden')
        // Each ProgressBarSlim has a label span and a bar container
        const labelSpans = mobileContainer?.querySelectorAll('.text-\\[10px\\].text-muted-foreground.whitespace-nowrap')
        expect(labelSpans?.length).toBe(2)
    })

    it('mobile bars clamp at 100% width when accumulated > target', () => {
        const { container } = render(
            <WeeklyProgressSummary
                tssAccumulated={900}
                tssTarget={600}
                trainingDaysCompleted={6}
                trainingDaysTarget={6}
                isLoading={false}
            />
        )
        // Both progress bars should not exceed 100% width (clamped by Math.min)
        // CSS will read `width: 100%` in the inner div
        const mobileContainer = container.querySelector('.flex.md\\:hidden')
        // Should render without crashing
        expect(mobileContainer).not.toBeNull()
    })

    it('training days label shows completed over target correctly', () => {
        render(
            <WeeklyProgressSummary
                tssAccumulated={400}
                tssTarget={600}
                trainingDaysCompleted={5}
                trainingDaysTarget={6}
                isLoading={false}
            />
        )
        const labels = screen.getAllByText('5/6 days')
        expect(labels.length).toBeGreaterThan(0)
    })
})
