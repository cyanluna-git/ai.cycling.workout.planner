/**
 * Convert workout steps JSON to chart data
 * 
 * Provides both legacy (fine-grained) and smooth (segment-based) data formats
 */

import type { WorkoutStep, ChartDataPoint } from '@/types/workout';

const RESOLUTION = 10; // 10-second resolution for legacy chart

function getZoneColor(power: number): string {
    if (power <= 55) return '#10b981';      // Z1 - Recovery
    if (power <= 75) return '#3b82f6';      // Z2 - Endurance
    if (power <= 90) return '#22c55e';      // Z3 - Tempo
    if (power <= 105) return '#eab308';     // Z4 - Threshold
    if (power <= 120) return '#f97316';     // Z5 - VO2max
    return '#ef4444';                        // Z6/Z7 - Anaerobic
}

/**
 * Convert steps to fine-grained chart data (10-second resolution)
 * Used by WorkoutChart for full-size display
 */
export function stepsToChartData(steps: WorkoutStep[]): ChartDataPoint[] {
    const chartData: ChartDataPoint[] = [];
    let currentTime = 0; // in seconds

    for (const step of steps) {
        const stepDuration = calculateStepDuration(step);
        processStep(step, currentTime, chartData);
        currentTime += stepDuration;
    }

    return chartData;
}

/**
 * Convert steps to smooth segment-based data for area chart
 * Used by WorkoutThumbnailChart for compact display
 */
export function stepsToSmoothData(steps: WorkoutStep[]): ChartDataPoint[] {
    const chartData: ChartDataPoint[] = [];
    let currentTime = 0; // in seconds

    for (const step of steps) {
        processStepSmooth(step, currentTime, chartData);
        currentTime += calculateStepDuration(step);
    }

    return chartData;
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

/**
 * Process step for fine-grained data (10-second blocks)
 */
function processStep(step: WorkoutStep, startTime: number, chartData: ChartDataPoint[]): void {
    const { duration, power, ramp, repeat, steps: nestedSteps } = step;

    // Handle repeat blocks
    if (repeat && nestedSteps) {
        let currentTime = startTime;
        for (let i = 0; i < repeat; i++) {
            for (const nestedStep of nestedSteps) {
                processStep(nestedStep, currentTime, chartData);
                currentTime += nestedStep.duration || 0;
            }
        }
        return;
    }

    if (!power) return;

    // Handle ramp steps
    if (ramp && power.start !== undefined && power.end !== undefined) {
        const steps = Math.max(1, Math.floor(duration / RESOLUTION));
        const powerDiff = power.end - power.start;

        for (let i = 0; i < steps; i++) {
            const progress = i / steps;
            const powerValue = Math.round(power.start + powerDiff * progress);

            chartData.push({
                time: (startTime + i * RESOLUTION) / 60,
                power: powerValue,
                color: getZoneColor(powerValue)
            });
        }

        // Handle remaining time
        const remainingTime = duration % RESOLUTION;
        if (remainingTime > 0.1) {
            const progress = steps / (steps + 1);
            const powerValue = Math.round(power.start + powerDiff * progress);
            chartData.push({
                time: (startTime + steps * RESOLUTION) / 60,
                power: powerValue,
                color: getZoneColor(powerValue)
            });
        }
    }
    // Handle steady state steps
    else if (power.value !== undefined) {
        const steps = Math.max(1, Math.floor(duration / RESOLUTION));
        const powerValue = power.value;

        for (let i = 0; i < steps; i++) {
            chartData.push({
                time: (startTime + i * RESOLUTION) / 60,
                power: powerValue,
                color: getZoneColor(powerValue)
            });
        }

        // Handle remaining time
        const remainingTime = duration % RESOLUTION;
        if (remainingTime > 0.1) {
            chartData.push({
                time: (startTime + steps * RESOLUTION) / 60,
                power: powerValue,
                color: getZoneColor(powerValue)
            });
        }
    }
}

/**
 * Process step for smooth area chart (segment endpoints only)
 */
function processStepSmooth(step: WorkoutStep, startTime: number, chartData: ChartDataPoint[]): void {
    const { duration, power, ramp, repeat, steps: nestedSteps } = step;

    // Handle repeat blocks
    if (repeat && nestedSteps) {
        let currentTime = startTime;
        for (let i = 0; i < repeat; i++) {
            for (const nestedStep of nestedSteps) {
                processStepSmooth(nestedStep, currentTime, chartData);
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
        chartData.push({
            time: startTimeMin,
            power: power.start,
            color: getZoneColor(power.start)
        });
        chartData.push({
            time: endTimeMin - 0.001,
            power: power.end,
            color: getZoneColor(power.end)
        });
    }
    // Handle steady state steps
    else if (power.value !== undefined) {
        chartData.push({
            time: startTimeMin,
            power: power.value,
            color: getZoneColor(power.value)
        });
        chartData.push({
            time: endTimeMin - 0.001,
            power: power.value,
            color: getZoneColor(power.value)
        });
    }
}
