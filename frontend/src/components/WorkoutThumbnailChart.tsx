/**
 * WorkoutThumbnailChart - Smooth power profile visualization
 * Renders workout power profile as a smooth filled area chart
 * like Intervals.icu style
 */

import React, { useMemo } from 'react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    ResponsiveContainer,
    ReferenceLine
} from 'recharts';
import { stepsToChartData } from '@/lib/steps-to-chart';
import type { WorkoutStep } from '@/types/workout';

interface WorkoutThumbnailChartProps {
    steps: WorkoutStep[];
    height?: number;
    showFTPLine?: boolean;
}

// Zone colors for gradient stops
const ZONE_GRADIENTS = {
    z1: '#10b981',  // Recovery - green
    z2: '#3b82f6',  // Endurance - blue
    z3: '#22c55e',  // Tempo - light green
    z4: '#eab308',  // Threshold - yellow
    z5: '#f97316',  // VO2max - orange
    z6: '#ef4444',  // Anaerobic - red
};

export const WorkoutThumbnailChart = React.memo(({
    steps,
    height = 70,
    showFTPLine = false
}: WorkoutThumbnailChartProps) => {
    // Convert steps to chart data (memoized for performance)
    const chartData = useMemo(() => {
        try {
            return stepsToChartData(steps);
        } catch (error) {
            console.error('Failed to convert steps to chart data:', error);
            return [];
        }
    }, [steps]);

    // Calculate max power for Y-axis scaling
    const maxPower = useMemo(() => {
        if (!chartData.length) return 100;
        return Math.max(...chartData.map(d => d.power), 100);
    }, [chartData]);

    if (!chartData || chartData.length === 0) {
        return (
            <div
                className="flex items-center justify-center bg-gray-100 rounded text-xs text-gray-500"
                style={{ height: `${height}px` }}
            >
                No chart data
            </div>
        );
    }

    return (
        <ResponsiveContainer width="100%" height={height}>
            <AreaChart
                data={chartData}
                margin={{ top: 2, right: 2, bottom: 2, left: 2 }}
            >
                <defs>
                    {/* Gradient for smooth zone transitions */}
                    <linearGradient id="powerGradient" x1="0" y1="1" x2="0" y2="0">
                        <stop offset="0%" stopColor={ZONE_GRADIENTS.z1} stopOpacity={0.6} />
                        <stop offset="55%" stopColor={ZONE_GRADIENTS.z2} stopOpacity={0.7} />
                        <stop offset="75%" stopColor={ZONE_GRADIENTS.z3} stopOpacity={0.7} />
                        <stop offset="90%" stopColor={ZONE_GRADIENTS.z4} stopOpacity={0.8} />
                        <stop offset="100%" stopColor={ZONE_GRADIENTS.z5} stopOpacity={0.9} />
                    </linearGradient>
                    {/* Stroke gradient */}
                    <linearGradient id="strokeGradient" x1="0" y1="1" x2="0" y2="0">
                        <stop offset="0%" stopColor={ZONE_GRADIENTS.z1} />
                        <stop offset="55%" stopColor={ZONE_GRADIENTS.z2} />
                        <stop offset="75%" stopColor={ZONE_GRADIENTS.z3} />
                        <stop offset="90%" stopColor={ZONE_GRADIENTS.z4} />
                        <stop offset="100%" stopColor={ZONE_GRADIENTS.z5} />
                    </linearGradient>
                </defs>
                <XAxis dataKey="time" hide />
                <YAxis domain={[0, maxPower * 1.1]} hide />
                {showFTPLine && (
                    <ReferenceLine
                        y={100}
                        stroke="#888"
                        strokeDasharray="3 3"
                        strokeWidth={1}
                    />
                )}
                <Area
                    type="stepAfter"  // stepAfter for sharp power transitions
                    dataKey="power"
                    stroke="url(#strokeGradient)"
                    strokeWidth={1.5}
                    fill="url(#powerGradient)"
                    isAnimationActive={false}
                />
            </AreaChart>
        </ResponsiveContainer>
    );
});

WorkoutThumbnailChart.displayName = 'WorkoutThumbnailChart';
