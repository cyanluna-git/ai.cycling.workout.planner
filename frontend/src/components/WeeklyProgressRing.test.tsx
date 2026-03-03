/**
 * Tests for WeeklyProgressRing component
 *
 * Covers:
 * - SVG ring renders with correct structure
 * - Percentage text displayed correctly
 * - Clamped at 100% visually when value > max
 * - 0% shown when max is 0 (edge case)
 * - Label rendered when provided
 * - Mount animation: starts at full circumference
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, act } from '@testing-library/react'
import { WeeklyProgressRing } from './WeeklyProgressRing'

describe('WeeklyProgressRing', () => {
    beforeEach(() => {
        vi.useFakeTimers()
    })

    afterEach(() => {
        vi.useRealTimers()
    })

    it('renders two SVG circles (background + progress)', () => {
        const { container } = render(
            <WeeklyProgressRing value={50} max={100} color="#06b6d4" />
        )
        const circles = container.querySelectorAll('circle')
        expect(circles.length).toBe(2)
    })

    it('shows percentage text in center', () => {
        const { container } = render(
            <WeeklyProgressRing value={50} max={100} color="#06b6d4" />
        )
        const percentageSpan = container.querySelector('.text-\\[10px\\].font-semibold')
        expect(percentageSpan?.textContent).toBe('50%')
    })

    it('shows 0% when max is 0', () => {
        const { container } = render(
            <WeeklyProgressRing value={0} max={0} color="#06b6d4" />
        )
        const percentageSpan = container.querySelector('.text-\\[10px\\].font-semibold')
        expect(percentageSpan?.textContent).toBe('0%')
    })

    it('shows actual percentage (>100) when value exceeds max in text', () => {
        const { container } = render(
            <WeeklyProgressRing value={150} max={100} color="#06b6d4" />
        )
        const percentageSpan = container.querySelector('.text-\\[10px\\].font-semibold')
        expect(percentageSpan?.textContent).toBe('150%')
    })

    it('clamps visual progress at 100% even when value > max', () => {
        const { container } = render(
            <WeeklyProgressRing value={200} max={100} size={64} strokeWidth={5} color="#06b6d4" />
        )
        // After animation fires
        act(() => {
            vi.advanceTimersByTime(100)
        })

        const progressCircle = container.querySelectorAll('circle')[1]
        const dashOffset = parseFloat(progressCircle.getAttribute('stroke-dashoffset') || '0')
        // At 100% clamp, offset should be 0 (fully drawn)
        expect(dashOffset).toBe(0)
    })

    it('renders label text when label prop is provided', () => {
        const { container } = render(
            <WeeklyProgressRing value={50} max={100} color="#06b6d4" label="680/850 TSS" />
        )
        const labelSpan = container.querySelector('.text-muted-foreground')
        expect(labelSpan?.textContent).toBe('680/850 TSS')
    })

    it('does not render label span when label is not provided', () => {
        const { container } = render(
            <WeeklyProgressRing value={50} max={100} color="#06b6d4" />
        )
        const labelSpans = container.querySelectorAll('.text-muted-foreground')
        expect(labelSpans.length).toBe(0)
    })

    it('applies custom size to SVG element', () => {
        const { container } = render(
            <WeeklyProgressRing value={50} max={100} size={80} color="#06b6d4" />
        )
        const svg = container.querySelector('svg')
        expect(svg?.getAttribute('width')).toBe('80')
        expect(svg?.getAttribute('height')).toBe('80')
    })

    it('progress circle has stroke color matching the color prop', () => {
        const { container } = render(
            <WeeklyProgressRing value={50} max={100} color="#f59e0b" />
        )
        const progressCircle = container.querySelectorAll('circle')[1]
        expect(progressCircle.getAttribute('stroke')).toBe('#f59e0b')
    })

    it('starts with ring fully undrawn (mount animation)', () => {
        const { container } = render(
            <WeeklyProgressRing value={50} max={100} size={64} strokeWidth={5} color="#06b6d4" />
        )
        const progressCircle = container.querySelectorAll('circle')[1]
        const dashArray = parseFloat(progressCircle.getAttribute('stroke-dasharray') || '0')
        const dashOffset = parseFloat(progressCircle.getAttribute('stroke-dashoffset') || '0')
        // Initially, offset should equal circumference (fully undrawn)
        expect(dashOffset).toBeCloseTo(dashArray, 0)
    })

    // -----------------------------------------------------------------------
    // Shield additions — additional edge cases
    // -----------------------------------------------------------------------

    it('shows 0% when value is 0 and max is positive', () => {
        const { container } = render(
            <WeeklyProgressRing value={0} max={100} color="#06b6d4" />
        )
        const percentageSpan = container.querySelector('.text-\\[10px\\].font-semibold')
        expect(percentageSpan?.textContent).toBe('0%')
    })

    it('animates to correct partial offset after timer fires (25% progress)', () => {
        const size = 64
        const strokeWidth = 5
        const { container } = render(
            <WeeklyProgressRing value={25} max={100} size={size} strokeWidth={strokeWidth} color="#06b6d4" />
        )
        act(() => {
            vi.advanceTimersByTime(100)
        })
        const progressCircle = container.querySelectorAll('circle')[1]
        const dashArray = parseFloat(progressCircle.getAttribute('stroke-dasharray') || '0')
        const dashOffset = parseFloat(progressCircle.getAttribute('stroke-dashoffset') || '0')
        // 25% progress: offset = circumference * 0.75
        const expectedOffset = dashArray * 0.75
        expect(dashOffset).toBeCloseTo(expectedOffset, 0)
    })

    it('uses default size of 64 when size prop is omitted', () => {
        const { container } = render(
            <WeeklyProgressRing value={50} max={100} color="#06b6d4" />
        )
        const svg = container.querySelector('svg')
        expect(svg?.getAttribute('width')).toBe('64')
        expect(svg?.getAttribute('height')).toBe('64')
    })

    it('progress circle has strokeLinecap="round" for rounded ends', () => {
        const { container } = render(
            <WeeklyProgressRing value={50} max={100} color="#06b6d4" />
        )
        const progressCircle = container.querySelectorAll('circle')[1]
        expect(progressCircle.getAttribute('stroke-linecap')).toBe('round')
    })

    it('progress circle has CSS transition style for smooth animation', () => {
        const { container } = render(
            <WeeklyProgressRing value={50} max={100} color="#06b6d4" />
        )
        const progressCircle = container.querySelectorAll('circle')[1]
        const style = progressCircle.getAttribute('style') || ''
        expect(style).toContain('transition')
    })

    it('renders to 100% (fully drawn) when value equals max after animation', () => {
        const { container } = render(
            <WeeklyProgressRing value={100} max={100} size={64} strokeWidth={5} color="#06b6d4" />
        )
        act(() => {
            vi.advanceTimersByTime(100)
        })
        const progressCircle = container.querySelectorAll('circle')[1]
        const dashOffset = parseFloat(progressCircle.getAttribute('stroke-dashoffset') || '999')
        expect(dashOffset).toBeCloseTo(0, 0)
    })
})
