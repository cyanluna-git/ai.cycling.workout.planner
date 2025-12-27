/**
 * API client for AI Cycling Coach backend
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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

export interface AthleteProfile {
    ftp: number | null;
    max_hr: number | null;
    lthr: number | null;
    weight: number | null;
    w_per_kg: number | null;
}

export interface FitnessData {
    training: TrainingMetrics;
    wellness: WellnessMetrics;
    profile: AthleteProfile;
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
    design_goal?: string;
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

export async function fetchFitness(token: string): Promise<FitnessData> {
    const res = await fetch(`${API_BASE}/api/fitness`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Failed to fetch fitness data');
    return res.json();
}

export async function checkApiConfigured(token: string): Promise<boolean> {
    try {
        const res = await fetch(`${API_BASE}/api/settings`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return false;
        const data = await res.json();
        return data.api_keys_configured === true;
    } catch {
        return false;
    }
}

export async function generateWorkout(
    request: WorkoutGenerateRequest,
    token: string
): Promise<{
    success: boolean;
    workout?: GeneratedWorkout;
    error?: string;
}> {
    const res = await fetch(`${API_BASE}/api/workout/generate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(request),
    });
    if (!res.ok) throw new Error('Failed to generate workout');
    return res.json();
}

export async function createWorkout(
    data: {
        target_date: string;
        name: string;
        workout_text: string;
        duration_minutes: number;
        estimated_tss?: number | null;
        force?: boolean;
    },
    token: string
): Promise<{
    success: boolean;
    event_id?: number;
    error?: string;
}> {
    const res = await fetch(`${API_BASE}/api/workout/create`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create workout');
    return res.json();
}

// --- Weekly Calendar ---

export interface WeeklyEvent {
    id: number;
    date: string;
    name: string;
    category: string;
    workout_type: string | null;
    duration_minutes: number | null;
    tss: number | null;
    description: string | null;
}

export interface WeeklyCalendarData {
    week_start: string;
    week_end: string;
    events: WeeklyEvent[];
}

export async function fetchWeeklyCalendar(token: string): Promise<WeeklyCalendarData> {
    const res = await fetch(`${API_BASE}/api/weekly-calendar`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Failed to fetch weekly calendar');
    return res.json();
}
