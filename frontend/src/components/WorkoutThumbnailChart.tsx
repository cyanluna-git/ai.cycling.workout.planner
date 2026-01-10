/**
 * WorkoutThumbnailChart - Compact power profile visualization
 * Optimized for 60-80px height display in weekly plan list
 */

import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, ResponsiveContainer, Cell } from 'recharts';
import { stepsToChartData } from '@/lib/steps-to-chart';
import type { WorkoutStep } from '@/types/workout';

interface WorkoutThumbnailChartProps {
    steps: WorkoutStep[];
    height?: number;
}

export const WorkoutThumbnailChart = React.memo(({
    steps,
    height = 70
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
            <BarChart
                data={chartData}
                margin={{ top: 2, right: 2, bottom: 2, left: 2 }}
            >
                <XAxis
                    dataKey="time"
                    hide
                />
                <Bar
                    dataKey="power"
                    isAnimationActive={false}  // Disable animation for performance
                    radius={[1, 1, 0, 0]}
                >
                    {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                </Bar>
            </BarChart>
        </ResponsiveContainer>
    );
});

WorkoutThumbnailChart.displayName = 'WorkoutThumbnailChart';
