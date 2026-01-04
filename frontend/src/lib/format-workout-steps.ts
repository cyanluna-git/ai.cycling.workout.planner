/**
 * Format workout steps for display
 */

import type { WorkoutStep } from '@/types/workout';

export interface FormattedStep {
    text: string;
    color: string;
}

export interface WorkoutSections {
    warmup: FormattedStep[];
    main: FormattedStep[];
    cooldown: FormattedStep[];
}

/**
 * Get zone color based on power percentage
 */
function getZoneColor(power: number): string {
    if (power <= 55) return '#10b981';      // Z1
    if (power <= 75) return '#3b82f6';      // Z2
    if (power <= 90) return '#22c55e';      // Z3
    if (power <= 105) return '#eab308';     // Z4
    if (power <= 120) return '#f97316';     // Z5
    return '#ef4444';                        // Z6/Z7
}

/**
 * Format a single step to text with watts
 */
function formatStepText(step: WorkoutStep, ftp: number): FormattedStep {
    const duration_min = Math.round(step.duration / 60);

    // Handle ramp steps
    if (step.ramp && step.power?.start !== undefined && step.power?.end !== undefined) {
        const startPower = step.power.start;
        const endPower = step.power.end;
        const startWatts = Math.round(ftp * startPower / 100);
        const endWatts = Math.round(ftp * endPower / 100);

        const maxPower = Math.max(startPower, endPower);
        const color = getZoneColor(maxPower);

        return {
            text: `${duration_min}m ${startPower}% (${startWatts}w) → ${endPower}% (${endWatts}w)`,
            color
        };
    }

    // Handle steady state
    if (step.power?.value !== undefined) {
        const power = step.power.value;
        const watts = Math.round(ftp * power / 100);
        const color = getZoneColor(power);

        return {
            text: `${duration_min}m ${power}% (${watts}w)`,
            color
        };
    }

    // Handle repeat blocks
    if (step.repeat && step.steps) {
        const nestedTexts = step.steps.map(s => formatStepText(s, ftp).text);
        const nestedStr = nestedTexts.join(' / ');

        // Find max power for color
        let maxPower = 0;
        step.steps.forEach(s => {
            if (s.ramp && s.power?.end !== undefined) {
                maxPower = Math.max(maxPower, s.power.end);
            } else if (s.power?.value !== undefined) {
                maxPower = Math.max(maxPower, s.power.value);
            }
        });
        const color = getZoneColor(maxPower);

        return {
            text: `${step.repeat}x (${nestedStr})`,
            color
        };
    }

    // Fallback
    return {
        text: `${duration_min}m`,
        color: '#888'
    };
}

/**
 * Extract and format workout sections from steps
 */
export function formatWorkoutSections(steps: WorkoutStep[], ftp: number = 250): WorkoutSections {
    const warmup: FormattedStep[] = [];
    const main: FormattedStep[] = [];
    const cooldown: FormattedStep[] = [];

    let inCooldown = false;

    for (const step of steps) {
        const formatted = formatStepText(step, ftp);

        // Detect section
        if (step.warmup) {
            warmup.push(formatted);
        } else if (step.cooldown) {
            cooldown.push(formatted);
            inCooldown = true;
        } else {
            // If we haven't hit cooldown yet, it's main set
            if (inCooldown) {
                cooldown.push(formatted);
            } else {
                main.push(formatted);
            }
        }
    }

    return { warmup, main, cooldown };
}
