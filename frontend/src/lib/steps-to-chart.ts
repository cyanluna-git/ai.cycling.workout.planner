/**
 * Convert workout steps JSON to chart data
 */

import type { WorkoutStep, ChartDataPoint } from '@/types/workout';

const RESOLUTION = 10; // 10-second resolution for chart

function getZoneColor(power: number): string {
    if (power <= 55) return '#10b981';      // Z1
    if (power <= 75) return '#3b82f6';      // Z2
    if (power <= 90) return '#22c55e';      // Z3
    if (power <= 105) return '#eab308';     // Z4
    if (power <= 120) return '#f97316';     // Z5
    return '#ef4444';                        // Z6/Z7
}

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

function calculateStepDuration(step: WorkoutStep): number {
    // For repeat blocks, calculate total duration from nested steps
    if (step.repeat && step.steps) {
        const nestedDuration = step.steps.reduce((sum, nestedStep) => {
            return sum + calculateStepDuration(nestedStep);
        }, 0);
        return nestedDuration * step.repeat;
    }

    // For regular steps, use the duration field
    return step.duration || 0;
}

function processStep(step: WorkoutStep, startTime: number, chartData: ChartDataPoint[]): void {
    const { duration, power, ramp, repeat, steps: nestedSteps } = step;

    // Handle repeat blocks
    if (repeat && nestedSteps) {
        let currentTime = startTime;
        for (let i = 0; i < repeat; i++) {
            for (const nestedStep of nestedSteps) {
                processStep(nestedStep, currentTime, chartData);
                currentTime += nestedStep.duration;
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
                time: (startTime + i * RESOLUTION) / 60, // Convert to minutes
                power: powerValue,
                color: getZoneColor(powerValue)
            });
        }

        // Handle any remaining time
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
