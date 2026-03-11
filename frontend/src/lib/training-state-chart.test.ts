import { describe, expect, it } from 'vitest';
import {
    getCenteredTrainingStateScore,
    getTrainingStateZone,
    mapTrainingHistoryForCenteredChart,
} from './training-state-chart';

describe('training-state-chart', () => {
    it('keeps the optimal midpoint near zero display state', () => {
        expect(getCenteredTrainingStateScore(-2.5)).toBe(0);
    });

    it('maps heavy negative TSB values into overload display space', () => {
        expect(getCenteredTrainingStateScore(-20)).toBeGreaterThan(0);
        expect(getTrainingStateZone(-20)).toBe('overload');
    });

    it('maps positive TSB values into need-load display space', () => {
        expect(getCenteredTrainingStateScore(10)).toBeLessThan(0);
        expect(getTrainingStateZone(10)).toBe('need_load');
    });

    it('maps history points with resolved labels for the centered chart', () => {
        const mapped = mapTrainingHistoryForCenteredChart(
            [{ date: '2026-03-11', ctl: 50, atl: 55, tsb: -6 }],
            {
                overload: 'Overload Risk',
                optimal: 'Optimal',
                need_load: 'Need Load',
            },
        );

        expect(mapped).toHaveLength(1);
        expect(mapped[0].state_zone).toBe('optimal');
        expect(mapped[0].state_label).toBe('Optimal');
        expect(mapped[0].display_state).toBeGreaterThan(-100);
        expect(mapped[0].display_state).toBeLessThan(100);
    });
});
