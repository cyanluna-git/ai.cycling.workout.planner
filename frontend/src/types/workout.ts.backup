/**
 * Shared workout step type definitions
 */

export interface PowerSpec {
    value?: number;      // For steady state (e.g., 80% FTP)
    start?: number;      // For ramps (start power)
    end?: number;        // For ramps (end power)
    units: string;       // Usually "%ftp"
}

export interface WorkoutStep {
    duration: number;           // Duration in seconds
    power?: PowerSpec;          // Power specification
    ramp?: boolean;             // True if this is a ramp (warmup/cooldown)
    warmup?: boolean;           // True if this is warmup section
    cooldown?: boolean;         // True if this is cooldown section
    repeat?: number;            // Number of repetitions (for intervals)
    steps?: WorkoutStep[];      // Nested steps (for repeat blocks)
    text?: string;              // Optional text description
}

/**
 * Chart data point for visualization
 */
export interface ChartDataPoint {
    time: number;      // Time in minutes
    power: number;     // Power in % FTP
    color: string;     // Zone color
}
