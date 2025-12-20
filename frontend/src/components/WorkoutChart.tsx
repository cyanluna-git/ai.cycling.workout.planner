import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';

interface WorkoutStep {
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
    ftp?: number;
}

/**
 * Parse workout text into chart data
 */
export function parseWorkoutSteps(text: string): WorkoutStep[] {
    const steps: WorkoutStep[] = [];
    let currentTime = 0;

    // Split by lines or commas
    const lines = text.split(/[\n,]/).map(l => l.trim()).filter(l => l);

    for (const line of lines) {
        // Match patterns like "10m 50%", "5m 65%", etc.
        const simpleMatch = line.match(/(\d+)m\s+(\d+)%/);

        // Match interval pattern: "5x 3m 115% 3m 50%"
        const intervalMatch = line.match(/(\d+)x\s+(\d+)m\s+(\d+)%\s+(\d+)m\s+(\d+)%/);

        if (intervalMatch) {
            const reps = parseInt(intervalMatch[1]);
            const workDuration = parseInt(intervalMatch[2]);
            const workPower = parseInt(intervalMatch[3]);
            const restDuration = parseInt(intervalMatch[4]);
            const restPower = parseInt(intervalMatch[5]);

            for (let i = 0; i < reps; i++) {
                steps.push({
                    time: currentTime,
                    duration: workDuration,
                    power: workPower,
                    label: `${workDuration}m ${workPower}%`
                });
                currentTime += workDuration;

                steps.push({
                    time: currentTime,
                    duration: restDuration,
                    power: restPower,
                    label: `${restDuration}m ${restPower}%`
                });
                currentTime += restDuration;
            }
        } else if (simpleMatch) {
            const duration = parseInt(simpleMatch[1]);
            const power = parseInt(simpleMatch[2]);

            steps.push({
                time: currentTime,
                duration,
                power,
                label: `${duration}m ${power}%`
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
function stepsToBarData(steps: WorkoutStep[]): ChartSegment[] {
    return steps.map(step => ({
        start: step.time,
        end: step.time + step.duration,
        power: step.power,
        color: getZoneColor(step.power)
    }));
}

export function WorkoutChart({ workoutText }: WorkoutChartProps) {
    const steps = parseWorkoutSteps(workoutText);
    const segments = stepsToBarData(steps);

    if (segments.length === 0) {
        return null;
    }

    const maxTime = segments[segments.length - 1]?.end || 60;
    const maxPower = Math.max(...segments.map(s => s.power), 100);

    // Create fine-grained data for better visualization (1 minute resolution)
    const barData: { time: number; power: number; color: string }[] = [];
    for (let t = 0; t < maxTime; t++) {
        const segment = segments.find(s => t >= s.start && t < s.end);
        if (segment) {
            barData.push({
                time: t,
                power: segment.power,
                color: segment.color
            });
        }
    }

    return (
        <div className="w-full h-32">
            <ResponsiveContainer width="100%" height="100%">
                <BarChart
                    data={barData}
                    margin={{ top: 5, right: 10, left: 10, bottom: 5 }}
                    barCategoryGap={0}
                >
                    <XAxis
                        dataKey="time"
                        type="number"
                        domain={[0, maxTime]}
                        tickFormatter={(v) => `${v}m`}
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
