/**
 * WorkoutThumbnailChart - Smooth zone-colored power profile
 * Uses ComposedChart with areas for each segment, colored by power zone
 */

import React, { useMemo } from 'react';
import {
    ComposedChart,
    Area,
    XAxis,
    YAxis,
    ResponsiveContainer,
    ReferenceLine
} from 'recharts';
import type { WorkoutStep } from '@/types/workout';

interface WorkoutThumbnailChartProps {
    steps: WorkoutStep[];
    height?: number;
    showFTPLine?: boolean;
}

function getZoneColor(power: number): string {
    if (power <= 55) return '#10b981';      // Z1 - Recovery (green)
    if (power <= 75) return '#3b82f6';      // Z2 - Endurance (blue)
    if (power <= 90) return '#22c55e';      // Z3 - Tempo (light green)
    if (power <= 105) return '#eab308';     // Z4 - Threshold (yellow)
    if (power <= 120) return '#f97316';     // Z5 - VO2max (orange)
    return '#ef4444';                        // Z6+ - Anaerobic (red)
}

interface Segment {
    startTime: number;  // minutes
    endTime: number;    // minutes
    power: number;      // %FTP
    color: string;
}

/**
 * Convert steps to segments for chart rendering
 */
function stepsToSegments(steps: WorkoutStep[]): Segment[] {
    const segments: Segment[] = [];

    function processStep(step: WorkoutStep, startTime: number): number {
        const { duration = 0, power, ramp, repeat, steps: nested } = step;

        // Handle repeat blocks
        if (repeat && nested) {
            let time = startTime;
            for (let i = 0; i < repeat; i++) {
                for (const ns of nested) {
                    time = processStep(ns, time);
                }
            }
            return time;
        }

        if (!power || !duration) return startTime;

        const startMin = startTime / 60;
        const endMin = (startTime + duration) / 60;

        if (ramp && power.start !== undefined && power.end !== undefined) {
            // Split ramp into multiple segments for gradient visualization
            const RAMP_RESOLUTION = 10; // 10 seconds per segment for smooth gradient
            const numSegments = Math.max(1, Math.floor(duration / RAMP_RESOLUTION));
            const segmentDuration = (endMin - startMin) / numSegments;
            const powerStep = (power.end - power.start) / numSegments;

            for (let i = 0; i < numSegments; i++) {
                const segPower = power.start + powerStep * (i + 0.5);
                segments.push({
                    startTime: startMin + segmentDuration * i,
                    endTime: startMin + segmentDuration * (i + 1),
                    power: segPower,
                    color: getZoneColor(segPower)
                });
            }
        } else if (power.value !== undefined) {
            segments.push({
                startTime: startMin,
                endTime: endMin,
                power: power.value,
                color: getZoneColor(power.value)
            });
        }

        return startTime + duration;
    }

    let time = 0;
    for (const step of steps) {
        time = processStep(step, time);
    }

    return segments;
}

export const WorkoutThumbnailChart = React.memo(({
    steps,
    height = 70,
    showFTPLine = false
}: WorkoutThumbnailChartProps) => {
    // Convert steps to segments
    const segments = useMemo(() => {
        try {
            return stepsToSegments(steps);
        } catch (error) {
            console.error('Failed to convert steps:', error);
            return [];
        }
    }, [steps]);

    // Group segments by zone color for rendering
    const chartData = useMemo((): { data: Record<string, number | string>[]; colors: string[] } => {
        if (segments.length === 0) {
            return { data: [], colors: [] };
        }

        // Get all unique colors
        const colors = [...new Set(segments.map(s => s.color))];
        const maxTime = Math.max(...segments.map(s => s.endTime));
        const data: Record<string, number | string>[] = [];

        // Create time points every 10 seconds (0.167 minutes) for smooth rendering
        const resolution = 10 / 60; // 10 seconds in minutes
        for (let t = 0; t <= maxTime; t += resolution) {
            const point: Record<string, number | string> = { time: t };

            // Find which segment this time falls into
            const activeSegment = segments.find(s => t >= s.startTime && t < s.endTime);

            // Set all zone values to 0 by default
            for (const color of colors) {
                point[color] = 0;
            }

            // Set the active zone's value
            if (activeSegment) {
                point[activeSegment.color] = activeSegment.power;
            }

            data.push(point);
        }

        return { data, colors };
    }, [segments]);

    const maxPower = useMemo(() => {
        if (segments.length === 0) return 100;
        return Math.max(...segments.map(s => s.power), 100);
    }, [segments]);

    if (!segments.length) {
        return (
            <div
                className="flex items-center justify-center bg-gray-100 rounded text-xs text-gray-500"
                style={{ height: `${height}px` }}
            >
                No data
            </div>
        );
    }

    return (
        <ResponsiveContainer width="100%" height={height}>
            <ComposedChart
                data={chartData.data}
                margin={{ top: 2, right: 2, bottom: 2, left: 2 }}
            >
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
                {/* Render an Area for each zone color */}
                {chartData.colors.map((color: string) => (
                    <Area
                        key={color}
                        type="stepAfter"
                        dataKey={color}
                        fill={color}
                        fillOpacity={0.85}
                        stroke="none"
                        isAnimationActive={false}
                        stackId="power"
                    />
                ))}
            </ComposedChart>
        </ResponsiveContainer>
    );
});

WorkoutThumbnailChart.displayName = 'WorkoutThumbnailChart';
