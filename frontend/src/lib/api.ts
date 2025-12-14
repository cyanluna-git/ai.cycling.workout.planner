/**
 * API client for AI Cycling Coach backend
 */

const API_BASE = import.meta.env.VITE_API_URL || '';

// --- Types ---

export interface TrainingMetrics {
    ctl: number;
    atl: number;
    tsb: number;
    form_status: string;
}

export interface WellnessMetrics {
    readiness: string;
    hrv: number | null;
    rhr: number | null;
    sleep_hours: number | null;
}

export interface FitnessData {
    training: TrainingMetrics;
    wellness: WellnessMetrics;
}

export interface GeneratedWorkout {
    name: string;
    workout_type: string;
    estimated_tss: number | null;
    estimated_duration_minutes: number;
    workout_text: string;
    warmup: string[];
    main: string[];
    cooldown: string[];
}

export interface WorkoutGenerateRequest {
    target_date?: string;
    duration: number;
    style: string;
    intensity: string;
    notes: string;
    indoor: boolean;
}

// --- API Functions ---

export async function fetchFitness(): Promise<FitnessData> {
    const res = await fetch(`${API_BASE}/api/fitness`);
    if (!res.ok) throw new Error('Failed to fetch fitness data');
    return res.json();
}

export async function generateWorkout(request: WorkoutGenerateRequest): Promise<{
    success: boolean;
    workout?: GeneratedWorkout;
    error?: string;
}> {
    const res = await fetch(`${API_BASE}/api/workout/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    });
    if (!res.ok) throw new Error('Failed to generate workout');
    return res.json();
}

export async function createWorkout(data: {
    target_date: string;
    name: string;
    workout_text: string;
    duration_minutes: number;
    estimated_tss?: number | null;
    force?: boolean;
}): Promise<{
    success: boolean;
    event_id?: number;
    error?: string;
}> {
    const res = await fetch(`${API_BASE}/api/workout/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create workout');
    return res.json();
}
