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
    fetchWeeklyPlan,
    generateWeeklyPlan,
    deleteWeeklyPlan,
    registerWeeklyPlanToIntervals,
    type FitnessData,
    type GeneratedWorkout,
    type WorkoutGenerateRequest,
    type WeeklyCalendarData,
    type WeeklyPlan,
} from "@/lib/api";

interface DashboardState {
    isApiConfigured: boolean | null;
    fitness: FitnessData | null;
    workout: GeneratedWorkout | null;
    weeklyCalendar: WeeklyCalendarData | null;
    weeklyPlan: WeeklyPlan | null;
    currentWeekOffset: number; // -1 = previous week, 0 = current week, 1 = next week
    isLoadingCalendar: boolean;
    isLoadingPlan: boolean;
    isGeneratingPlan: boolean;
    isRegisteringPlanAll: boolean;
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
    handleGenerateWeeklyPlan: () => Promise<void>;
    handleDeleteWeeklyPlan: (planId: string) => Promise<void>;
    handleRegisterWeeklyPlanAll: (planId: string) => Promise<void>;
    handleWeekNavigation: (direction: 'prev' | 'next') => Promise<void>;
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
    const [weeklyPlan, setWeeklyPlan] = useState<WeeklyPlan | null>(null);
    const [currentWeekOffset, setCurrentWeekOffset] = useState(0); // 0 = current week by default
    const [isLoadingCalendar, setIsLoadingCalendar] = useState(false);
    const [isLoadingPlan, setIsLoadingPlan] = useState(false);
    const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);
    const [isRegisteringPlanAll, setIsRegisteringPlanAll] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [isRegistering, setIsRegistering] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // Helper function to calculate Monday of a week with offset
    const getWeekStartDate = useCallback((offset: number): string => {
        const today = new Date();
        const dayOfWeek = today.getDay(); // 0 = Sunday, 1 = Monday, ...
        const daysToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek; // How many days until Monday
        const monday = new Date(today);
        monday.setDate(today.getDate() + daysToMonday + (offset * 7));
        return monday.toISOString().split('T')[0];
    }, []);

    // Fetch weekly plan for current offset
    const fetchWeeklyPlanForOffset = useCallback(async (offset: number) => {
        if (!session?.access_token) return;

        setIsLoadingPlan(true);
        try {
            const weekStartDate = getWeekStartDate(offset);
            const plan = await fetchWeeklyPlan(session.access_token, weekStartDate);
            setWeeklyPlan(plan);
        } catch (e) {
            console.error(e);
            setWeeklyPlan(null);
        } finally {
            setIsLoadingPlan(false);
        }
    }, [session, getWeekStartDate]);

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

            // Fetch weekly plan for current offset
            fetchWeeklyPlanForOffset(currentWeekOffset);
        }
    }, [session, isApiConfigured, currentWeekOffset, fetchWeeklyPlanForOffset]);

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

    const handleGenerateWeeklyPlan = useCallback(async () => {
        if (!session?.access_token) {
            setError("인증 토큰이 없습니다.");
            return;
        }

        // Prevent double-clicks/rapid requests
        if (isGeneratingPlan) {
            return;
        }

        setIsGeneratingPlan(true);
        setError(null);
        setSuccess(null);

        try {
            const plan = await generateWeeklyPlan(session.access_token);
            setWeeklyPlan(plan);
            setSuccess("✅ 주간 워크아웃 계획이 생성되었습니다!");
        } catch (e) {
            const errorMsg = e instanceof Error ? e.message : String(e);
            // Check for rate limit errors
            if (errorMsg.includes('rate_limit') || errorMsg.includes('429')) {
                setError(`⏱️ API 사용량 한도 도달. 잠시 후 다시 시도해주세요.`);
            } else {
                setError(`주간 계획 생성 실패: ${errorMsg}`);
            }
        } finally {
            setIsGeneratingPlan(false);
        }
    }, [session, isGeneratingPlan]);

    const handleDeleteWeeklyPlan = useCallback(async (planId: string) => {
        if (!session?.access_token) {
            setError("인증 토큰이 없습니다.");
            return;
        }

        try {
            await deleteWeeklyPlan(session.access_token, planId);
            setWeeklyPlan(null);
            setSuccess("주간 계획이 삭제되었습니다.");
        } catch (e) {
            setError(`삭제 실패: ${e instanceof Error ? e.message : String(e)}`);
        }
    }, [session]);

    const handleRegisterWeeklyPlanAll = useCallback(async (planId: string) => {
        if (!session?.access_token) {
            setError("인증 토큰이 없습니다.");
            return;
        }

        setIsRegisteringPlanAll(true);
        setError(null);
        setSuccess(null);

        try {
            const result = await registerWeeklyPlanToIntervals(session.access_token, planId);
            setSuccess(`${result.registered}개의 워크아웃이 Intervals.icu에 등록되었습니다.`);

            if (result.failed > 0) {
                setError(`${result.failed}개의 워크아웃 등록 실패`);
            }
        } catch (e) {
            setError(`등록 실패: ${e instanceof Error ? e.message : String(e)}`);
        } finally {
            setIsRegisteringPlanAll(false);
        }
    }, [session]);

    const handleWeekNavigation = useCallback(async (direction: 'prev' | 'next') => {
        const newOffset = direction === 'next' ? currentWeekOffset + 1 : currentWeekOffset - 1;
        setCurrentWeekOffset(newOffset);
    }, [currentWeekOffset]);

    return {
        // State
        isApiConfigured,
        fitness,
        workout,
        weeklyCalendar,
        weeklyPlan,
        currentWeekOffset,
        isLoadingCalendar,
        isLoadingPlan,
        isGeneratingPlan,
        isRegisteringPlanAll,
        isLoading,
        isRegistering,
        error,
        success,
        // Actions
        handleGenerate,
        handleRegister,
        handleSelectDate,
        handleOnboardingComplete,
        handleGenerateWeeklyPlan,
        handleDeleteWeeklyPlan,
        handleRegisterWeeklyPlanAll,
        handleWeekNavigation,
        clearMessages,
    };
}
