/**
 * WorkoutChart - Full-size smooth zone-colored power profile
 * Uses ComposedChart with areas for each segment, colored by power zone
 */

import { useMemo } from 'react';
import {
    ComposedChart,
    Area,
    XAxis,
    YAxis,
    ResponsiveContainer,
    ReferenceLine
} from 'recharts';
import { parseZwoToChartData, type ChartDataPoint } from '@/lib/zwo-parser';
import type { WorkoutStep } from '@/types/workout';

interface WorkoutChartProps {
    workoutText: string;
    zwoContent?: string;
    steps?: WorkoutStep[];
    ftp?: number;
}

export function getZoneColor(power: number): string {
    if (power <= 55) return '#10b981';      // Z1 - Recovery (green)
    if (power <= 75) return '#3b82f6';      // Z2 - Endurance (blue)
    if (power <= 90) return '#22c55e';      // Z3 - Tempo (light green)
    if (power <= 105) return '#eab308';     // Z4 - Threshold (yellow)
    if (power <= 120) return '#f97316';     // Z5 - VO2 Max (orange)
    return '#ef4444';                        // Z6/Z7 - Anaerobic (red)
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
                const segPower = power.start + powerStep * (i + 0.5); // Use midpoint power
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

/**
 * Convert ZWO chart data to segments
 */
function chartDataToSegments(chartData: ChartDataPoint[]): Segment[] {
    if (chartData.length === 0) return [];

    const segments: Segment[] = [];
    let currentPower = chartData[0].power;
    let startTime = chartData[0].time;

    for (let i = 1; i < chartData.length; i++) {
        const point = chartData[i];
        if (point.power !== currentPower) {
            segments.push({
                startTime,
                endTime: point.time,
                power: currentPower,
                color: getZoneColor(currentPower)
            });
            currentPower = point.power;
            startTime = point.time;
        }
    }

    // Add final segment
    const lastPoint = chartData[chartData.length - 1];
    segments.push({
        startTime,
        endTime: lastPoint.time + 0.5,
        power: currentPower,
        color: getZoneColor(currentPower)
    });

    return segments;
}

export function WorkoutChart({ zwoContent, steps }: WorkoutChartProps) {
    // Convert to segments
    const segments = useMemo((): Segment[] => {
        if (steps && steps.length > 0) {
            return stepsToSegments(steps);
        } else if (zwoContent) {
            const chartData = parseZwoToChartData(zwoContent);
            return chartDataToSegments(chartData);
        }
        return [];
    }, [steps, zwoContent]);

    // Group segments by zone color for rendering
    const chartData = useMemo((): { data: Record<string, number | string>[]; colors: string[] } => {
        if (segments.length === 0) {
            return { data: [], colors: [] };
        }

        const colors = [...new Set(segments.map(s => s.color))];
        const maxTime = Math.max(...segments.map(s => s.endTime));
        const data: Record<string, number | string>[] = [];

        // Create time points every 10 seconds (0.167 minutes) for smooth rendering
        const resolution = 10 / 60; // 10 seconds in minutes
        for (let t = 0; t <= maxTime; t += resolution) {
            const point: Record<string, number | string> = { time: t };

            const activeSegment = segments.find(s => t >= s.startTime && t < s.endTime);

            for (const color of colors) {
                point[color] = 0;
            }

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

    const maxTime = useMemo(() => {
        if (segments.length === 0) return 60;
        return Math.max(...segments.map(s => s.endTime));
    }, [segments]);

    if (chartData.data.length === 0) {
        return null;
    }

    return (
        <div className="w-full h-32" style={{ minHeight: 128, minWidth: 100 }}>
            <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={128}>
                <ComposedChart
                    data={chartData.data}
                    margin={{ top: 5, right: 10, left: 10, bottom: 5 }}
                >
                    <XAxis
                        dataKey="time"
                        type="number"
                        domain={[0, maxTime]}
                        tickFormatter={(v) => `${Math.round(v)}m`}
                        tick={{ fontSize: 10, fill: '#888' }}
                        axisLine={{ stroke: '#444' }}
                        tickLine={{ stroke: '#444' }}
                    />
                    <YAxis
                        domain={[0, Math.ceil(maxPower / 20) * 20 + 20]}
                        tickFormatter={(v) => `${v}%`}
                        tick={{ fontSize: 10, fill: '#888' }}
                        axisLine={{ stroke: '#444' }}
                        tickLine={{ stroke: '#444' }}
                        width={40}
                    />
                    <ReferenceLine
                        y={100}
                        stroke="#ef4444"
                        strokeDasharray="3 3"
                        strokeOpacity={0.7}
                        label={{ value: 'F', position: 'right', fontSize: 10, fill: '#ef4444' }}
                    />
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
        </div>
    );
}
