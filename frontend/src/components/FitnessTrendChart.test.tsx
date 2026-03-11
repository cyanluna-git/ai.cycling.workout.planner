import { beforeAll, describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { FitnessTrendChart } from './FitnessTrendChart';
import { FitnessCard } from './FitnessCard';
import type { AthleteProfile, TrainingHistoryPoint, TrainingMetrics, WellnessMetrics } from '@/lib/api';
import enLocale from '../i18n/locales/en.json';
import koLocale from '../i18n/locales/ko.json';

beforeAll(() => {
    if (typeof globalThis.ResizeObserver === 'undefined') {
        globalThis.ResizeObserver = class {
            observe() {}
            unobserve() {}
            disconnect() {}
        };
    }
});

const makeHistory = (tsb: number[] = [8, 4, -3, -8, -14, -6, 2]): TrainingHistoryPoint[] =>
    tsb.map((value, index) => ({
        date: `2026-03-${String(index + 5).padStart(2, '0')}`,
        ctl: 48 + index,
        atl: 52 + index,
        tsb: value,
    }));

const mockTraining: TrainingMetrics = {
    ctl: 60,
    atl: 55,
    tsb: -6,
    form_status: 'Moderate',
};

const mockWellness: WellnessMetrics = {
    readiness: 'Good',
    hrv: 70,
    hrv_sdnn: null,
    rhr: 52,
    sleep_hours: 7.5,
    sleep_score: null,
    sleep_quality: null,
    weight: 70,
    body_fat: null,
    vo2max: null,
    soreness: null,
    fatigue: null,
    stress: null,
    mood: null,
    motivation: null,
    spo2: null,
    systolic: null,
    diastolic: null,
    respiration: null,
    readiness_score: null,
    active_calories_load: null,
    active_calories_history: null,
};

const mockProfile: AthleteProfile = {
    ftp: 250,
    max_hr: 185,
    lthr: 165,
    weight: 70,
    w_per_kg: 3.57,
    vo2max: 52.3,
};

describe('i18n locale files — centered trend chart keys', () => {
    it('en.json contains centered trend keys', () => {
        const fitness = (enLocale as Record<string, unknown>).fitness as Record<string, unknown>;
        expect(fitness.trendStateLabel).toBe('Training State');
        expect(typeof fitness.centeredTrendHint).toBe('string');
        expect(typeof fitness.centeredTrendGlossary).toBe('string');
    });

    it('ko.json contains centered trend keys', () => {
        const fitness = (koLocale as Record<string, unknown>).fitness as Record<string, unknown>;
        expect(fitness.trendStateLabel).toBe('훈련 상태');
        expect(typeof fitness.centeredTrendHint).toBe('string');
        expect(typeof fitness.centeredTrendGlossary).toBe('string');
    });
});

describe('FitnessTrendChart', () => {
    it('renders centered legend copy and hint', () => {
        render(<FitnessTrendChart history={makeHistory()} />);

        expect(screen.getByText('Overload risk when TSB stays too low')).toBeInTheDocument();
        expect(screen.getByText('Optimal band centered around balanced form')).toBeInTheDocument();
        expect(screen.getByText('Need load when TSB trends too fresh')).toBeInTheDocument();
        expect(screen.getByText(/This chart centers the optimal TSB band/i)).toBeInTheDocument();
    });

    it('mounts without throwing when history is empty', () => {
        expect(() => render(<FitnessTrendChart history={[]} />)).not.toThrow();
    });
});

describe('FitnessCard — centered trend integration', () => {
    it('still hides the trend section when ctl_history is missing', () => {
        render(
            <FitnessCard
                training={mockTraining}
                wellness={mockWellness}
                profile={mockProfile}
            />,
        );

        expect(screen.queryByText('7-Day Trend')).toBeNull();
    });

    it('renders the centered training glossary entry when chart data exists', () => {
        render(
            <FitnessCard
                training={{ ...mockTraining, ctl_history: makeHistory() }}
                wellness={mockWellness}
                profile={mockProfile}
            />,
        );

        expect(screen.getByText('7-Day Trend')).toBeInTheDocument();
        expect(screen.getByText(/This chart centers the optimal TSB band/i)).toBeInTheDocument();
    });
});
