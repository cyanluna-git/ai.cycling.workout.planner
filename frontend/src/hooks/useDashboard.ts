/**
 * useDashboard Hook
 * 
 * Manages state and business logic for the Dashboard component.
 * Separates concerns between data/logic and presentation.
 */

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import {
    fetchFitness,
    generateWorkout,
    createWorkout,
    fetchWeeklyCalendar,
    fetchTodaysWorkout,
    checkApiConfigured,
    type FitnessData,
    type GeneratedWorkout,
    type WorkoutGenerateRequest,
    type WeeklyCalendarData,
} from "@/lib/api";

interface DashboardState {
    isApiConfigured: boolean | null;
    fitness: FitnessData | null;
    workout: GeneratedWorkout | null;
    weeklyCalendar: WeeklyCalendarData | null;
    isLoadingCalendar: boolean;
    isLoading: boolean;
    isRegistering: boolean;
    error: string | null;
    success: string | null;
}

interface DashboardActions {
    handleGenerate: (request: WorkoutGenerateRequest) => Promise<void>;
    handleRegister: () => Promise<void>;
    handleSelectDate: (date: string) => Promise<void>;
    handleOnboardingComplete: () => void;
    clearMessages: () => void;
}

export type UseDashboardReturn = DashboardState & DashboardActions;

export function useDashboard(): UseDashboardReturn {
    const { session } = useAuth();

    // State
    const [isApiConfigured, setIsApiConfigured] = useState<boolean | null>(null);
    const [fitness, setFitness] = useState<FitnessData | null>(null);
    const [workout, setWorkout] = useState<GeneratedWorkout | null>(null);
    const [weeklyCalendar, setWeeklyCalendar] = useState<WeeklyCalendarData | null>(null);
    const [isLoadingCalendar, setIsLoadingCalendar] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [isRegistering, setIsRegistering] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // Check if API is configured
    useEffect(() => {
        if (session?.access_token) {
            checkApiConfigured(session.access_token)
                .then(setIsApiConfigured);
        }
    }, [session]);

    // Fetch data only if API is configured
    useEffect(() => {
        if (session?.access_token && isApiConfigured) {
            fetchFitness(session.access_token)
                .then(setFitness)
                .catch((e) => setError(`데이터 로딩 실패: ${e.message}`));

            setIsLoadingCalendar(true);
            fetchWeeklyCalendar(session.access_token)
                .then((data) => {
                    setWeeklyCalendar(data);
                    return fetchTodaysWorkout(session.access_token);
                })
                .then((result) => {
                    if (result && result.success && result.workout) {
                        setWorkout(result.workout);
                        setSuccess("📅 오늘의 워크아웃을 불러왔습니다.");
                    }
                })
                .catch(console.error)
                .finally(() => setIsLoadingCalendar(false));
        }
    }, [session, isApiConfigured]);

    // Actions
    const handleOnboardingComplete = useCallback(() => {
        setIsApiConfigured(true);
    }, []);

    const handleGenerate = useCallback(async (request: WorkoutGenerateRequest) => {
        setIsLoading(true);
        setError(null);
        setSuccess(null);
        setWorkout(null);

        try {
            if (!session?.access_token) {
                setError("인증 토큰이 없습니다. 다시 로그인해주세요.");
                return;
            }
            const result = await generateWorkout(request, session.access_token);
            if (result.success && result.workout) {
                setWorkout(result.workout);
            } else {
                setError(result.error || "워크아웃 생성 실패");
            }
        } catch (e) {
            setError(`생성 오류: ${e instanceof Error ? e.message : String(e)}`);
        } finally {
            setIsLoading(false);
        }
    }, [session]);

    const handleRegister = useCallback(async () => {
        if (!workout) return;

        setIsRegistering(true);
        setError(null);

        try {
            if (!session?.access_token) {
                setError("인증 토큰이 없습니다.");
                return;
            }
            const today = new Date().toISOString().split("T")[0];
            const result = await createWorkout(
                {
                    target_date: today,
                    name: workout.name,
                    workout_text: workout.workout_text,
                    duration_minutes: workout.estimated_duration_minutes,
                    estimated_tss: workout.estimated_tss,
                    design_goal: workout.design_goal,
                    workout_type: workout.workout_type,
                    force: true,
                    steps: workout.steps,
                },
                session.access_token
            );

            if (result.success) {
                setSuccess(`✅ 등록 완료! (Event ID: ${result.event_id})`);
            } else {
                setError(result.error || "등록 실패");
            }
        } catch (e) {
            setError(`등록 오류: ${e instanceof Error ? e.message : String(e)}`);
        } finally {
            setIsRegistering(false);
        }
    }, [session, workout]);

    const handleSelectDate = useCallback(async (date: string) => {
        if (!session?.access_token) return;

        setIsLoading(true);
        setError(null);
        setSuccess(null);
        setWorkout(null);

        try {
            const result = await fetchTodaysWorkout(session.access_token, date);
            if (result.success && result.workout) {
                setWorkout(result.workout);
                setSuccess(`📅 ${date} 워크아웃을 불러왔습니다.`);
            } else {
                setError(`${date}에는 저장된 워크아웃이 없습니다.`);
            }
        } catch (e) {
            setError(`불러오기 실패: ${e instanceof Error ? e.message : String(e)}`);
        } finally {
            setIsLoading(false);
        }
    }, [session]);

    const clearMessages = useCallback(() => {
        setError(null);
        setSuccess(null);
    }, []);

    return {
        // State
        isApiConfigured,
        fitness,
        workout,
        weeklyCalendar,
        isLoadingCalendar,
        isLoading,
        isRegistering,
        error,
        success,
        // Actions
        handleGenerate,
        handleRegister,
        handleSelectDate,
        handleOnboardingComplete,
        clearMessages,
    };
}
