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
    // Basic metrics
    readiness: string;
    hrv: number | null;
    hrv_sdnn: number | null;
    rhr: number | null;
    sleep_hours: number | null;
    sleep_score: number | null;
    sleep_quality: number | null;

    // Physical state
    weight: number | null;
    body_fat: number | null;
    vo2max: number | null;

    // Subjective ratings (1-5 scale)
    soreness: number | null;
    fatigue: number | null;
    stress: number | null;
    mood: number | null;
    motivation: number | null;

    // Health metrics
    spo2: number | null;
    systolic: number | null;
    diastolic: number | null;
    respiration: number | null;

    // Computed/derived
    readiness_score: number | null;
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
    steps?: any[]; // JSON steps for Intervals.icu
    zwo_content?: string; // ZWO XML content for chart rendering
}

export interface WorkoutGenerateRequest {
    target_date?: string;
    duration: number;
    style: string;
    intensity: string;
    notes: string;
    indoor: boolean;
}

// --- Sport Settings ---

export interface PowerZone {
    id: number;
    name: string;
    min_watts: number | null;
    max_watts: number | null;
}

export interface HRZone {
    id: number;
    name: string;
    min_bpm: number | null;
    max_bpm: number | null;
}

export interface SportSettings {
    // Power settings
    ftp: number | null;
    eftp: number | null;
    ftp_source: string | null;

    // Heart rate settings
    max_hr: number | null;
    lthr: number | null;
    resting_hr: number | null;

    // Zones
    power_zones: PowerZone[];
    hr_zones: HRZone[];

    // Other metrics
    weight: number | null;
    w_per_kg: number | null;
    pace_threshold: number | null;

    // Sport type
    sport_types: string[];
}

// --- API Functions ---

export async function fetchFitness(token: string): Promise<FitnessData> {
    const res = await fetch(`${API_BASE}/api/fitness`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Failed to fetch fitness data');
    return res.json();
}

export async function fetchSportSettings(token: string, sport: string = 'Ride'): Promise<SportSettings> {
    const res = await fetch(`${API_BASE}/api/sport-settings?sport=${sport}`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Failed to fetch sport settings');
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
        design_goal?: string;
        workout_type?: string;
        force?: boolean;
        steps?: any[];
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

export async function fetchTodaysWorkout(token: string, date?: string): Promise<{
    success: boolean;
    workout?: GeneratedWorkout;
    error?: string;
}> {
    let url = `${API_BASE}/api/workout/today`;
    if (date) {
        url += `?date=${date}`;
    }

    const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Failed to fetch today\'s workout');
    return res.json();
}

// --- Weekly Calendar ---

export interface WeeklyEvent {
    id: string; // Changed to string
    date: string;
    name: string;
    category: string;
    workout_type: string | null;
    duration_minutes: number | null;
    tss: number | null;
    description: string | null;
    is_actual?: boolean;
    is_indoor?: boolean;
}

export interface WeeklyCalendarData {
    week_start: string;
    week_end: string;
    events: WeeklyEvent[];
    planned_tss: number;
    actual_tss: number;
}

export async function fetchWeeklyCalendar(token: string): Promise<WeeklyCalendarData> {
    const res = await fetch(`${API_BASE}/api/weekly-calendar`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Failed to fetch weekly calendar');
    return res.json();
}
