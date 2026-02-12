/**
 * API client for AI Cycling Coach backend
 */

import type { WorkoutStep } from '@/types/workout';
import i18n from '@/i18n/config';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function getHeaders(token?: string, contentType?: string): HeadersInit {
    const headers: HeadersInit = {
        'Accept-Language': i18n.language || 'ko',
    };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (contentType) headers['Content-Type'] = contentType;
    return headers;
}

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
    vo2max: number | null;
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
    steps?: WorkoutStep[]; // Structured workout steps (strongly typed)
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

export async function fetchFitness(token: string, refresh: boolean = false): Promise<FitnessData> {
    const url = refresh ? `${API_BASE}/api/fitness?refresh=true` : `${API_BASE}/api/fitness`;
    const res = await fetch(url, {
        headers: getHeaders(token),
    });
    if (!res.ok) throw new Error('Failed to fetch fitness data');
    return res.json();
}

export async function fetchSportSettings(token: string, sport: string = 'Ride'): Promise<SportSettings> {
    const res = await fetch(`${API_BASE}/api/sport-settings?sport=${sport}`, {
        headers: getHeaders(token),
    });
    if (!res.ok) throw new Error('Failed to fetch sport settings');
    return res.json();
}

export async function checkApiConfigured(token: string): Promise<boolean> {
    try {
        const res = await fetch(`${API_BASE}/api/settings`, {
            headers: getHeaders(token),
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
        headers: getHeaders(token, 'application/json'),
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
        steps?: WorkoutStep[];
    },
    token: string
): Promise<{
    success: boolean;
    event_id?: number;
    error?: string;
}> {
    const res = await fetch(`${API_BASE}/api/workout/create`, {
        method: 'POST',
        headers: getHeaders(token, 'application/json'),
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
        headers: getHeaders(token),
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
        headers: getHeaders(token),
    });
    if (!res.ok) throw new Error('Failed to fetch weekly calendar');
    return res.json();
}

// --- Weekly Plan (New Feature) ---

export interface DailyWorkout {
    id?: string;
    workout_date: string;
    day_name: string;
    planned_name?: string;
    planned_type?: string;
    planned_duration?: number;
    planned_tss?: number;
    planned_rationale?: string;
    planned_modules?: string[];          // Module keys for power profile
    planned_steps?: WorkoutStep[];       // WorkoutStep[] for chart rendering
    actual_name?: string;
    actual_type?: string;
    status: string;
    session?: string;  // "AM", "PM", or null for single session (Norwegian style)
}

export interface WeeklyPlan {
    id: string;
    week_start: string;
    week_end: string;
    status: string;
    training_style?: string;
    total_planned_tss?: number;
    weekly_tss_target?: number;
    total_actual_tss?: number;
    achievement_status?: string;  // achieved/exceeded/partial/missed/in_progress/no_target
    achievement_pct?: number;
    daily_workouts: DailyWorkout[];
}

export interface AchievementBadge {
    id: string;
    name: string;
    icon: string;
    desc_key: string;
    type: string;
    requirement: number;
    remaining?: number;
}

export interface AchievementsData {
    current_streak: number;
    best_streak: number;
    total_achieved_weeks: number;
    total_exceeded_weeks: number;
    earned_badges: AchievementBadge[];
    next_badge: AchievementBadge | null;
    weekly_history: Array<{
        week_start: string;
        week_end: string;
        weekly_tss_target: number | null;
        total_actual_tss: number | null;
        achievement_status: string;
        achievement_pct: number;
    }>;
}

export interface TodayWorkout {
    has_plan: boolean;
    workout?: DailyWorkout;
    wellness_hint?: string;
    can_regenerate: boolean;
    // Weekly TSS tracking
    weekly_tss_target?: number;
    weekly_tss_accumulated?: number;
    weekly_tss_remaining?: number;
    days_remaining_in_week?: number;
    target_achievable?: boolean;
    achievement_warning?: string;
}

export async function fetchWeeklyPlan(token: string, weekStartDate?: string): Promise<WeeklyPlan | null> {
    const url = weekStartDate
        ? `${API_BASE}/api/plans/weekly?week_start_date=${weekStartDate}`
        : `${API_BASE}/api/plans/weekly`;
    const res = await fetch(url, {
        headers: getHeaders(token),
    });
    if (!res.ok) throw new Error('Failed to fetch weekly plan');
    const data = await res.json();
    return data;
}

export async function generateWeeklyPlan(
    token: string,
    weekStart?: string,
    weeklyTssTarget?: number
): Promise<WeeklyPlan> {
    const body: Record<string, unknown> = { week_start: weekStart };
    if (weeklyTssTarget !== undefined) body.weekly_tss_target = weeklyTssTarget;
    const res = await fetch(`${API_BASE}/api/plans/weekly/generate`, {
        method: 'POST',
        headers: getHeaders(token, 'application/json'),
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to generate weekly plan');
    }
    return res.json();
}

export async function fetchTodayPlan(token: string): Promise<TodayWorkout> {
    const res = await fetch(`${API_BASE}/api/plans/today`, {
        headers: getHeaders(token),
    });
    if (!res.ok) throw new Error('Failed to fetch today plan');
    return res.json();
}

export async function regenerateTodayWorkout(
    token: string,
    reason?: string
): Promise<{ success: boolean; workout?: unknown }> {
    const res = await fetch(`${API_BASE}/api/plans/today/regenerate`, {
        method: 'POST',
        headers: getHeaders(token, 'application/json'),
        body: JSON.stringify({ reason }),
    });
    if (!res.ok) throw new Error('Failed to regenerate workout');
    return res.json();
}

export async function skipWorkout(
    token: string,
    workoutId: string
): Promise<{ success: boolean }> {
    const res = await fetch(`${API_BASE}/api/plans/daily/${workoutId}/skip`, {
        method: 'PUT',
        headers: getHeaders(token),
    });
    if (!res.ok) throw new Error('Failed to skip workout');
    return res.json();
}

export async function deleteWeeklyPlan(
    token: string,
    planId: string
): Promise<{ success: boolean }> {
    const res = await fetch(`${API_BASE}/api/plans/weekly/${planId}`, {
        method: 'DELETE',
        headers: getHeaders(token),
    });
    if (!res.ok) throw new Error('Failed to delete plan');
    return res.json();
}

export async function registerWeeklyPlanToIntervals(
    token: string,
    planId: string
): Promise<{ success: boolean; registered: number; failed: number; message: string }> {
    const res = await fetch(`${API_BASE}/api/plans/weekly/${planId}/register-all`, {
        method: 'POST',
        headers: getHeaders(token),
    });
    if (!res.ok) throw new Error('Failed to register plan to Intervals.icu');
    return res.json();
}

export interface SyncChange {
    date?: string;
    name?: string;
    event_id: string;
    from_date?: string;
    to_date?: string;
    old_name?: string;
    new_name?: string;
}

export interface SyncResult {
    success: boolean;
    changes: {
        deleted: SyncChange[];
        moved: SyncChange[];
        modified: SyncChange[];
    };
    synced: number;
    message: string;
}

export async function syncWeeklyPlanWithIntervals(
    token: string,
    planId: string
): Promise<SyncResult> {
    const res = await fetch(`${API_BASE}/api/plans/weekly/${planId}/sync`, {
        method: 'POST',
        headers: getHeaders(token),
    });
    if (!res.ok) throw new Error('Failed to sync with Intervals.icu');
    return res.json();
}

export async function fetchAchievements(token: string): Promise<AchievementsData> {
    const res = await fetch(`${API_BASE}/api/plans/achievements`, {
        headers: getHeaders(token),
    });
    if (!res.ok) throw new Error('Failed to fetch achievements');
    return res.json();
}

export async function finalizeWeeklyPlan(token: string, planId: string): Promise<{ success: boolean; achievement_status: string; achievement_pct: number }> {
    const res = await fetch(`${API_BASE}/api/plans/weekly/${planId}/finalize`, {
        method: 'POST',
        headers: getHeaders(token, 'application/json'),
    });
    if (!res.ok) throw new Error('Failed to finalize plan');
    return res.json();
}
