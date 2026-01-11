/**
 * Convert workout steps JSON to smooth chart data
 * 
 * Creates segment-based data points for smooth area chart rendering
 * instead of discrete 10-second bars
 */

import type { WorkoutStep, ChartDataPoint } from '@/types/workout';

function getZoneColor(power: number): string {
    if (power <= 55) return '#10b981';      // Z1 - Recovery
    if (power <= 75) return '#3b82f6';      // Z2 - Endurance
    if (power <= 90) return '#22c55e';      // Z3 - Tempo
    if (power <= 105) return '#eab308';     // Z4 - Threshold
    if (power <= 120) return '#f97316';     // Z5 - VO2max
    return '#ef4444';                        // Z6/Z7 - Anaerobic
}

interface SmoothChartSegment {
    startTime: number;    // in minutes
    endTime: number;      // in minutes
    startPower: number;   // %FTP
    endPower: number;     // %FTP
    color: string;
}

/**
 * Convert steps to smooth segment-based data for area chart
 */
export function stepsToSmoothSegments(steps: WorkoutStep[]): SmoothChartSegment[] {
    const segments: SmoothChartSegment[] = [];
    let currentTime = 0; // in seconds

    for (const step of steps) {
        processStepToSegment(step, currentTime, segments);
        currentTime += calculateStepDuration(step);
    }

    return segments;
}

/**
 * Convert segments to chart data points for smooth rendering
 * Uses minimal points: start and end of each segment
 */
export function segmentsToChartData(segments: SmoothChartSegment[]): ChartDataPoint[] {
    const chartData: ChartDataPoint[] = [];

    for (let i = 0; i < segments.length; i++) {
        const seg = segments[i];

        // Add start point
        chartData.push({
            time: seg.startTime,
            power: seg.startPower,
            color: seg.color
        });

        // For ramps, add intermediate points for smooth curve
        if (seg.startPower !== seg.endPower) {
            const midTime = (seg.startTime + seg.endTime) / 2;
            const midPower = (seg.startPower + seg.endPower) / 2;
            chartData.push({
                time: midTime,
                power: midPower,
                color: getZoneColor(midPower)
            });
        }

        // Add end point (slightly before to create sharp transition)
        chartData.push({
            time: seg.endTime - 0.001,
            power: seg.endPower,
            color: seg.color
        });
    }

    return chartData;
}

/**
 * Legacy function for backward compatibility
 * Still used by some components
 */
export function stepsToChartData(steps: WorkoutStep[]): ChartDataPoint[] {
    const segments = stepsToSmoothSegments(steps);
    return segmentsToChartData(segments);
}

function calculateStepDuration(step: WorkoutStep): number {
    if (step.repeat && step.steps) {
        const nestedDuration = step.steps.reduce((sum, nestedStep) => {
            return sum + calculateStepDuration(nestedStep);
        }, 0);
        return nestedDuration * step.repeat;
    }
    return step.duration || 0;
}

function processStepToSegment(
    step: WorkoutStep,
    startTime: number,
    segments: SmoothChartSegment[]
): void {
    const { duration, power, ramp, repeat, steps: nestedSteps } = step;

    // Handle repeat blocks
    if (repeat && nestedSteps) {
        let currentTime = startTime;
        for (let i = 0; i < repeat; i++) {
            for (const nestedStep of nestedSteps) {
                processStepToSegment(nestedStep, currentTime, segments);
                currentTime += nestedStep.duration || 0;
            }
        }
        return;
    }

    if (!power || !duration) return;

    const startTimeMin = startTime / 60;
    const endTimeMin = (startTime + duration) / 60;

    // Handle ramp steps
    if (ramp && power.start !== undefined && power.end !== undefined) {
        segments.push({
            startTime: startTimeMin,
            endTime: endTimeMin,
            startPower: power.start,
            endPower: power.end,
            color: getZoneColor((power.start + power.end) / 2)
        });
    }
    // Handle steady state steps
    else if (power.value !== undefined) {
        segments.push({
            startTime: startTimeMin,
            endTime: endTimeMin,
            startPower: power.value,
            endPower: power.value,
            color: getZoneColor(power.value)
        });
    }
}
