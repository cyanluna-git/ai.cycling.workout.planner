/**
 * ProfileChart — Zwift-style power profile visualization
 *
 * Renders steps_json as a zone-colored area chart using Recharts.
 * Reuses zone color logic from WorkoutChart.
 */

import { useMemo } from 'react';
import {
    ComposedChart,
    Area,
    XAxis,
    YAxis,
    ResponsiveContainer,
    ReferenceLine,
} from 'recharts';

interface StepPower {
    value?: number;
    start?: number;
    end?: number;
    units?: string;
}

interface Step {
    type?: string;
    duration_sec?: number;
    power?: number;
    start_power?: number;
    end_power?: number;
    on_power?: number;
    off_power?: number;
    on_sec?: number;
    off_sec?: number;
    repeat?: number;
    // Frontend format fields
    duration?: number;
    ramp?: boolean;
    warmup?: boolean;
    cooldown?: boolean;
    steps?: Step[];
}

interface StepsJson {
    steps?: Step[];
}

interface ProfileChartProps {
    stepsJson: StepsJson | Step[] | null;
    height?: number;
    className?: string;
}

function getZoneColor(power: number): string {
    if (power <= 55) return '#009e80';   // Z1 - Recovery
    if (power <= 75) return '#009e00';   // Z2 - Endurance
    if (power <= 90) return '#ffcb0e';   // Z3 - Tempo
    if (power <= 105) return '#ff7f0e';  // Z4 - Threshold
    if (power <= 120) return '#dd0447';  // Z5 - VO2max
    return '#6633cc';                     // Z6 - Anaerobic
}

interface Segment {
    startTime: number;
    endTime: number;
    power: number;
    color: string;
}

function stepsToSegments(steps: Step[]): Segment[] {
    const segments: Segment[] = [];

    function processStep(step: Step, startTime: number): number {
        // Handle repeat blocks (DB format: repeat + on/off or frontend format: repeat + steps)
        if (step.repeat && step.repeat > 0) {
            // Frontend format: { repeat, steps: [...] }
            if (step.steps && step.steps.length > 0) {
                let time = startTime;
                for (let i = 0; i < step.repeat; i++) {
                    for (const ns of step.steps) {
                        time = processStep(ns, time);
                    }
                }
                return time;
            }
            // DB format: intervals with on/off
            if (step.on_sec && step.on_power !== undefined) {
                let time = startTime;
                for (let i = 0; i < step.repeat; i++) {
                    const onStart = time / 60;
                    const onEnd = (time + (step.on_sec || 0)) / 60;
                    segments.push({
                        startTime: onStart,
                        endTime: onEnd,
                        power: step.on_power || 0,
                        color: getZoneColor(step.on_power || 0),
                    });
                    time += step.on_sec || 0;

                    if (step.off_sec && step.off_power !== undefined) {
                        const offStart = time / 60;
                        const offEnd = (time + step.off_sec) / 60;
                        segments.push({
                            startTime: offStart,
                            endTime: offEnd,
                            power: step.off_power,
                            color: getZoneColor(step.off_power),
                        });
                        time += step.off_sec;
                    }
                }
                return time;
            }
        }

        const duration = step.duration_sec || step.duration || 0;
        if (!duration) return startTime;

        const startMin = startTime / 60;
        const endMin = (startTime + duration) / 60;

        // Ramp (DB format: start_power/end_power)
        if (step.start_power !== undefined && step.end_power !== undefined) {
            const numSeg = Math.max(1, Math.floor(duration / 10));
            const segDur = (endMin - startMin) / numSeg;
            const powerStep = (step.end_power - step.start_power) / numSeg;
            for (let i = 0; i < numSeg; i++) {
                const p = step.start_power + powerStep * (i + 0.5);
                segments.push({
                    startTime: startMin + segDur * i,
                    endTime: startMin + segDur * (i + 1),
                    power: p,
                    color: getZoneColor(p),
                });
            }
        }
        // Ramp (frontend format: power.start/power.end)
        else if (step.ramp && typeof step.power === 'object') {
            const pw = step.power as unknown as StepPower;
            if (pw.start !== undefined && pw.end !== undefined) {
                const numSeg = Math.max(1, Math.floor(duration / 10));
                const segDur = (endMin - startMin) / numSeg;
                const powerSt = (pw.end - pw.start) / numSeg;
                for (let i = 0; i < numSeg; i++) {
                    const p = pw.start + powerSt * (i + 0.5);
                    segments.push({
                        startTime: startMin + segDur * i,
                        endTime: startMin + segDur * (i + 1),
                        power: p,
                        color: getZoneColor(p),
                    });
                }
            }
        }
        // Steady power (DB format: power as number)
        else if (typeof step.power === 'number') {
            segments.push({
                startTime: startMin,
                endTime: endMin,
                power: step.power,
                color: getZoneColor(step.power),
            });
        }
        // Frontend format: power.value
        else if (typeof step.power === 'object') {
            const pw = step.power as unknown as StepPower;
            if (pw.value !== undefined) {
                segments.push({
                    startTime: startMin,
                    endTime: endMin,
                    power: pw.value,
                    color: getZoneColor(pw.value),
                });
            }
        }

        return startTime + duration;
    }

    let time = 0;
    for (const step of steps) {
        time = processStep(step, time);
    }
    return segments;
}

export function ProfileChart({ stepsJson, height = 160, className = '' }: ProfileChartProps) {
    const segments = useMemo((): Segment[] => {
        if (!stepsJson) return [];
        const steps = Array.isArray(stepsJson) ? stepsJson : stepsJson.steps || [];
        if (steps.length === 0) return [];
        return stepsToSegments(steps);
    }, [stepsJson]);

    const chartData = useMemo(() => {
        if (segments.length === 0) return { data: [] as Record<string, number | string>[], colors: [] as string[] };

        const colors = [...new Set(segments.map(s => s.color))];
        const maxTime = Math.max(...segments.map(s => s.endTime));
        const data: Record<string, number | string>[] = [];
        const resolution = 10 / 60; // 10 seconds

        for (let t = 0; t <= maxTime; t += resolution) {
            const point: Record<string, number | string> = { time: t };
            for (const color of colors) {
                point[color] = 0;
            }
            const active = segments.find(s => t >= s.startTime && t < s.endTime);
            if (active) {
                point[active.color] = active.power;
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
        return <div className={`flex items-center justify-center text-muted-foreground text-sm ${className}`} style={{ height }}>No chart data</div>;
    }

    return (
        <div className={`w-full bg-[#1a1a2e] rounded-lg p-2 ${className}`} style={{ height }}>
            <ResponsiveContainer width="100%" height="100%">
                <ComposedChart
                    data={chartData.data}
                    margin={{ top: 5, right: 10, left: 10, bottom: 5 }}
                >
                    <XAxis
                        dataKey="time"
                        type="number"
                        domain={[0, maxTime]}
                        tickFormatter={(v) => `${Math.round(v)}m`}
                        tick={{ fontSize: 10, fill: '#666' }}
                        axisLine={{ stroke: '#333' }}
                        tickLine={{ stroke: '#333' }}
                    />
                    <YAxis
                        domain={[0, Math.ceil(maxPower / 20) * 20 + 20]}
                        tickFormatter={(v) => `${v}%`}
                        tick={{ fontSize: 10, fill: '#666' }}
                        axisLine={{ stroke: '#333' }}
                        tickLine={{ stroke: '#333' }}
                        width={40}
                    />
                    <ReferenceLine
                        y={100}
                        stroke="#ef4444"
                        strokeDasharray="3 3"
                        strokeOpacity={0.5}
                        label={{ value: 'FTP', position: 'right', fontSize: 9, fill: '#ef4444' }}
                    />
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
