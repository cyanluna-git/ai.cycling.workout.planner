import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';
import { parseZwoToChartData, getMaxTime, getMaxPower, type ChartDataPoint } from '@/lib/zwo-parser';
import { stepsToChartData } from '@/lib/steps-to-chart';
import type { WorkoutStep } from '@/types/workout';

// Legacy type for text parsing fallback (deprecated)
interface ParsedWorkoutStep {
    time: number;      // Start time in minutes
    duration: number;  // Duration of this step in minutes
    power: number;     // Power as % FTP
    label: string;     // Original text label
}

interface ChartSegment {
    start: number;
    end: number;
    power: number;
    color: string;
}

interface WorkoutChartProps {
    workoutText: string;
    zwoContent?: string;  // ZWO XML content for accurate rendering
    steps?: WorkoutStep[];  // Structured JSON steps from Intervals.icu (strongly typed)
    ftp?: number;
}

/**
 * Parse duration string to minutes
 */
function parseDuration(val: string, unit: string): number {
    const value = parseInt(val);
    if (unit === 's') return value / 60;
    return value;
}

/**
 * Parse workout text into chart data
 * @deprecated This is a fallback for when structured steps are not available.
 * With Intervals.icu as single source of truth, this should rarely be used.
 */
export function parseWorkoutSteps(text: string): ParsedWorkoutStep[] {
    const steps: ParsedWorkoutStep[] = [];
    let currentTime = 0;

    // Split by lines or commas
    const lines = text.split(/[\n,]/).map(l => l.trim()).filter(l => l);

    for (const line of lines) {
        // Match ramp pattern: "10m 45% -> 75%" (warmup/cooldown ramps)
        const rampMatch = line.match(/(\d+)([ms])\s+(\d+)%\s*->\s*(\d+)%/);

        // Match patterns like "10m 50%", "30s 120%"
        const simpleMatch = line.match(/(\d+)([ms])\s+(\d+)%/);

        // Match interval pattern: "5x 3m 115% 3m 50%" or "13x 30s 120% 15s 50%"
        const intervalMatch = line.match(/(\d+)x\s*\(?(\d+)([ms])\s+(\d+)%\s*[\/\s]+(\d+)([ms])\s+(\d+)%\)?/);

        if (rampMatch) {
            // Ramp: split into 10-second segments (1/6 min) for smooth visual
            const duration = parseDuration(rampMatch[1], rampMatch[2]);
            const startPower = parseInt(rampMatch[3]);
            const endPower = parseInt(rampMatch[4]);

            const SEGMENT_DURATION = 1 / 6;
            const stepsCount = Math.floor(duration / SEGMENT_DURATION);
            const powerStep = (endPower - startPower) / stepsCount;

            for (let i = 0; i < stepsCount; i++) {
                const power = Math.round(startPower + powerStep * i);
                steps.push({
                    time: currentTime,
                    duration: SEGMENT_DURATION,
                    power,
                    label: `Ramp ${power}%`
                });
                currentTime += SEGMENT_DURATION;
            }
            // Add any remaining partial segment
            if (duration % SEGMENT_DURATION > 0.001) {
                currentTime += (duration % SEGMENT_DURATION);
            }
        } else if (intervalMatch) {
            const reps = parseInt(intervalMatch[1]);
            const workDuration = parseDuration(intervalMatch[2], intervalMatch[3]);
            const workPower = parseInt(intervalMatch[4]);
            const restDuration = parseDuration(intervalMatch[5], intervalMatch[6]);
            const restPower = parseInt(intervalMatch[7]);

            for (let i = 0; i < reps; i++) {
                steps.push({
                    time: currentTime,
                    duration: workDuration,
                    power: workPower,
                    label: `${Math.round(workDuration * 60)}s ${workPower}%`
                });
                currentTime += workDuration;

                steps.push({
                    time: currentTime,
                    duration: restDuration,
                    power: restPower,
                    label: `${Math.round(restDuration * 60)}s ${restPower}%`
                });
                currentTime += restDuration;
            }
        } else if (simpleMatch) {
            const duration = parseDuration(simpleMatch[1], simpleMatch[2]);
            const power = parseInt(simpleMatch[3]);

            steps.push({
                time: currentTime,
                duration,
                power,
                label: `${Math.round(duration * 60)}s ${power}%`
            });
            currentTime += duration;
        }
    }

    return steps;
}

/**
 * Get zone color based on power percentage
 */
export function getZoneColor(power: number): string {
    if (power <= 55) return '#10b981';      // Z1 - Recovery (green)
    if (power <= 75) return '#3b82f6';      // Z2 - Endurance (blue)
    if (power <= 90) return '#22c55e';      // Z3 - Tempo (light green)
    if (power <= 105) return '#eab308';     // Z4 - Threshold (yellow)
    if (power <= 120) return '#f97316';     // Z5 - VO2 Max (orange)
    return '#ef4444';                        // Z6/Z7 - Anaerobic (red)
}

/**
 * Convert steps to bar chart data
 */
function stepsToBarData(steps: ParsedWorkoutStep[]): ChartSegment[] {
    return steps.map(step => ({
        start: step.time,
        end: step.time + step.duration,
        power: step.power,
        color: getZoneColor(step.power)
    }));
}

export function WorkoutChart({ workoutText, zwoContent, steps }: WorkoutChartProps) {
    // Priority: steps JSON > ZWO content > text parsing
    let barData: ChartDataPoint[] = [];
    let maxTime = 60;
    let maxPower = 100;

    if (steps && steps.length > 0) {
        // Use structured JSON steps from Intervals.icu (most accurate!)
        barData = stepsToChartData(steps);
        maxTime = getMaxTime(barData);
        maxPower = getMaxPower(barData);
    } else if (zwoContent) {
        // Use ZWO parser for accurate rendering
        barData = parseZwoToChartData(zwoContent);
        maxTime = getMaxTime(barData);
        maxPower = getMaxPower(barData);
    } else {
        // Fallback to text parsing (deprecated)
        console.warn('⚠️ WorkoutChart: Falling back to text parsing. Structured steps not available.');
        const workoutSteps = parseWorkoutSteps(workoutText);
        const segments = stepsToBarData(workoutSteps);

        if (segments.length === 0) {
            return null;
        }

        maxTime = segments[segments.length - 1]?.end || 60;
        maxPower = Math.max(...segments.map(s => s.power), 100);

        // Create fine-grained data for better visualization (10-second resolution)
        const RESOLUTION = 1 / 6; // 10 seconds in minutes

        for (let t = 0; t < maxTime; t += RESOLUTION) {
            // Find segment covering this time point (t + half-resolution to check center)
            const centerTime = t + (RESOLUTION / 2);
            const segment = segments.find(s => centerTime >= s.start && centerTime < s.end);

            if (segment) {
                barData.push({
                    time: t,
                    power: segment.power,
                    color: segment.color
                });
            }
        }
    }

    if (barData.length === 0) {
        return null;
    }

    return (
        <div className="w-full h-32" style={{ minHeight: 128, minWidth: 100 }}>
            <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={128}>
                <BarChart
                    data={barData}
                    margin={{ top: 5, right: 10, left: 10, bottom: 5 }}
                    barCategoryGap={0}
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
                        label={{ value: 'FTP', position: 'right', fontSize: 10, fill: '#ef4444' }}
                    />
                    <Bar dataKey="power" isAnimationActive={false}>
                        {barData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} fillOpacity={0.85} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
