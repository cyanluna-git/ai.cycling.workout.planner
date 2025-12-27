/**
 * ZWO Parser - Parses ZWO (Zwift Workout) XML to chart data
 */

export interface ZwoStep {
    type: 'steadystate' | 'warmup' | 'cooldown' | 'intervalst' | 'freeride';
    duration: number;  // seconds
    powerLow?: number; // decimal (0.5 = 50%)
    powerHigh?: number;
    repeat?: number;
    onDuration?: number;
    offDuration?: number;
    onPower?: number;
    offPower?: number;
}

export interface ChartDataPoint {
    time: number;     // minutes
    power: number;    // percentage
    color: string;
}

/**
 * Get zone color based on power percentage
 */
function getZoneColor(power: number): string {
    if (power <= 55) return '#10b981';      // Z1 - Recovery (green)
    if (power <= 75) return '#3b82f6';      // Z2 - Endurance (blue)
    if (power <= 90) return '#22c55e';      // Z3 - Tempo (light green)
    if (power <= 105) return '#eab308';     // Z4 - Threshold (yellow)
    if (power <= 120) return '#f97316';     // Z5 - VO2 Max (orange)
    return '#ef4444';                        // Z6/Z7 - Anaerobic (red)
}

/**
 * Parse ZWO XML content to chart data points
 */
export function parseZwoToChartData(zwoContent: string): ChartDataPoint[] {
    const parser = new DOMParser();
    const doc = parser.parseFromString(zwoContent, 'text/xml');

    const workout = doc.querySelector('workout');
    if (!workout) return [];

    const chartData: ChartDataPoint[] = [];
    let currentTime = 0;
    const RESOLUTION = 10; // 10-second resolution

    // Process each workout element
    const elements = workout.children;
    for (let i = 0; i < elements.length; i++) {
        const el = elements[i];
        const tagName = el.tagName.toLowerCase();

        if (tagName === 'steadystate') {
            const duration = parseInt(el.getAttribute('Duration') || '0');
            const power = parseFloat(el.getAttribute('Power') || '0.5') * 100;

            // Add data points at resolution intervals
            for (let t = 0; t < duration; t += RESOLUTION) {
                chartData.push({
                    time: (currentTime + t) / 60,
                    power: Math.round(power),
                    color: getZoneColor(power)
                });
            }
            currentTime += duration;

        } else if (tagName === 'warmup' || tagName === 'cooldown') {
            const duration = parseInt(el.getAttribute('Duration') || '0');
            const powerLow = parseFloat(el.getAttribute('PowerLow') || '0.4') * 100;
            const powerHigh = parseFloat(el.getAttribute('PowerHigh') || '0.7') * 100;
            const isWarmup = tagName === 'warmup';

            // Create ramp by interpolating power
            const steps = Math.floor(duration / RESOLUTION);
            for (let j = 0; j < steps; j++) {
                const progress = j / steps;
                const power = isWarmup
                    ? powerLow + (powerHigh - powerLow) * progress
                    : powerHigh - (powerHigh - powerLow) * progress;

                chartData.push({
                    time: (currentTime + j * RESOLUTION) / 60,
                    power: Math.round(power),
                    color: getZoneColor(power)
                });
            }
            currentTime += duration;

        } else if (tagName === 'intervalst') {
            const repeat = parseInt(el.getAttribute('Repeat') || '1');
            const onDuration = parseInt(el.getAttribute('OnDuration') || '60');
            const offDuration = parseInt(el.getAttribute('OffDuration') || '60');
            const onPower = parseFloat(el.getAttribute('OnPower') || '1.0') * 100;
            const offPower = parseFloat(el.getAttribute('OffPower') || '0.5') * 100;

            for (let r = 0; r < repeat; r++) {
                // On interval
                for (let t = 0; t < onDuration; t += RESOLUTION) {
                    chartData.push({
                        time: (currentTime + t) / 60,
                        power: Math.round(onPower),
                        color: getZoneColor(onPower)
                    });
                }
                currentTime += onDuration;

                // Off interval
                for (let t = 0; t < offDuration; t += RESOLUTION) {
                    chartData.push({
                        time: (currentTime + t) / 60,
                        power: Math.round(offPower),
                        color: getZoneColor(offPower)
                    });
                }
                currentTime += offDuration;
            }

        } else if (tagName === 'freeride') {
            const duration = parseInt(el.getAttribute('Duration') || '0');
            const power = 50; // Default free ride power

            for (let t = 0; t < duration; t += RESOLUTION) {
                chartData.push({
                    time: (currentTime + t) / 60,
                    power,
                    color: getZoneColor(power)
                });
            }
            currentTime += duration;
        }
    }

    return chartData;
}

/**
 * Get max time from chart data
 */
export function getMaxTime(chartData: ChartDataPoint[]): number {
    if (chartData.length === 0) return 0;
    return chartData[chartData.length - 1].time + (10 / 60); // Add one more resolution step
}

/**
 * Get max power from chart data
 */
export function getMaxPower(chartData: ChartDataPoint[]): number {
    if (chartData.length === 0) return 100;
    return Math.max(...chartData.map(d => d.power), 100);
}
