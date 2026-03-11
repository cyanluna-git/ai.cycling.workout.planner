import type { TrainingHistoryPoint } from '@/lib/api';

export type TrainingStateZone = 'overload' | 'optimal' | 'need_load';

export interface CenteredTrainingStatePoint extends TrainingHistoryPoint {
    display_state: number;
    state_zone: TrainingStateZone;
    state_label: string;
}

const OPTIMAL_CENTER_TSB = -2.5;
const OPTIMAL_LOWER_TSB = -10;
const OPTIMAL_UPPER_TSB = 5;
const DISPLAY_SCALE = 4;
const DISPLAY_LIMIT = 100;

function clamp(value: number, min: number, max: number): number {
    return Math.min(max, Math.max(min, value));
}

export function getCenteredTrainingStateScore(tsb: number): number {
    return clamp(
        (OPTIMAL_CENTER_TSB - tsb) * DISPLAY_SCALE,
        -DISPLAY_LIMIT,
        DISPLAY_LIMIT,
    );
}

export function getTrainingStateZone(tsb: number): TrainingStateZone {
    if (tsb < OPTIMAL_LOWER_TSB) return 'overload';
    if (tsb > OPTIMAL_UPPER_TSB) return 'need_load';
    return 'optimal';
}

export function mapTrainingHistoryForCenteredChart(
    history: TrainingHistoryPoint[],
    labels: Record<TrainingStateZone, string>,
): CenteredTrainingStatePoint[] {
    return history.map((point) => {
        const state_zone = getTrainingStateZone(point.tsb);
        return {
            ...point,
            display_state: getCenteredTrainingStateScore(point.tsb),
            state_zone,
            state_label: labels[state_zone],
        };
    });
}
