/**
 * useDashboard Hook with React Query
 *
 * Optimized data fetching with:
 * - Automatic caching (2 hour stale time)
 * - Parallel requests for independent data
 * - Optimistic UI updates
 * - Background refetching
 */

import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { queryKeys } from "@/lib/queryClient";
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
    currentWeekOffset: number;
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
    handleWeekNavigation: (direction: 'prev' | 'next') => void;
    clearMessages: () => void;
}

export type UseDashboardReturn = DashboardState & DashboardActions;

export function useDashboard(): UseDashboardReturn {
    const { session } = useAuth();
    const queryClient = useQueryClient();

    // Local state for UI feedback
    const [currentWeekOffset, setCurrentWeekOffset] = useState(0);
    const [workout, setWorkout] = useState<GeneratedWorkout | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isRegistering, setIsRegistering] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // Helper function to calculate Monday of a week with offset
    const getWeekStartDate = useCallback((offset: number): string => {
        const today = new Date();
        const dayOfWeek = today.getDay();
        const daysToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
        const monday = new Date(today);
        monday.setDate(today.getDate() + daysToMonday + (offset * 7));
        return monday.toISOString().split('T')[0];
    }, []);

    // Check if API is configured (cached for 5 minutes)
    const { data: isApiConfigured = null } = useQuery({
        queryKey: queryKeys.apiConfigured(),
        queryFn: () => checkApiConfigured(session?.access_token || ''),
        enabled: !!session?.access_token,
        staleTime: 5 * 60 * 1000, // 5 minutes
    });

    // Fetch fitness data (cached for 2 hours, matches backend)
    const { data: fitness = null } = useQuery({
        queryKey: queryKeys.fitness(),
        queryFn: () => fetchFitness(session?.access_token || ''),
        enabled: !!session?.access_token && isApiConfigured === true,
        staleTime: 2 * 60 * 60 * 1000, // 2 hours
    });

    // Fetch weekly calendar (cached for 2 hours)
    const {
        data: weeklyCalendar = null,
        isLoading: isLoadingCalendar,
    } = useQuery({
        queryKey: queryKeys.weeklyCalendar(),
        queryFn: () => fetchWeeklyCalendar(session?.access_token || ''),
        enabled: !!session?.access_token && isApiConfigured === true,
        staleTime: 2 * 60 * 60 * 1000, // 2 hours
    });

    // Fetch weekly plan (cached per week)
    const weekStartDate = getWeekStartDate(currentWeekOffset);
    const {
        data: weeklyPlan = null,
        isLoading: isLoadingPlan,
    } = useQuery({
        queryKey: queryKeys.weeklyPlan(weekStartDate),
        queryFn: () => fetchWeeklyPlan(session?.access_token || '', weekStartDate),
        enabled: !!session?.access_token && isApiConfigured === true,
        staleTime: 2 * 60 * 60 * 1000, // 2 hours
    });

    // Fetch today's workout (initially)
    const { data: todayWorkoutData } = useQuery({
        queryKey: queryKeys.todayWorkout(),
        queryFn: () => fetchTodaysWorkout(session?.access_token || ''),
        enabled: !!session?.access_token && isApiConfigured === true && !workout,
        staleTime: 1 * 60 * 60 * 1000, // 1 hour
        onSuccess: (result) => {
            if (result && result.success && result.workout) {
                setWorkout(result.workout);
                setSuccess("📅 오늘의 워크아웃을 불러왔습니다.");
            }
        },
    });

    // Mutations
    const generateMutation = useMutation({
        mutationFn: (request: WorkoutGenerateRequest) =>
            generateWorkout(request, session?.access_token || ''),
        onSuccess: (result) => {
            if (result.success && result.workout) {
                setWorkout(result.workout);
                setError(null);
            } else {
                setError(result.error || "워크아웃 생성 실패");
            }
        },
        onError: (e: Error) => {
            setError(`생성 오류: ${e.message}`);
        },
    });

    const registerMutation = useMutation({
        mutationFn: (data: {
            target_date: string;
            name: string;
            workout_text: string;
            duration_minutes: number;
            estimated_tss?: number | null;
            design_goal?: string;
            workout_type?: string;
            force?: boolean;
            steps?: any[];
        }) => createWorkout(data, session?.access_token || ''),
        onSuccess: (result) => {
            if (result.success) {
                setSuccess(`✅ 등록 완료! (Event ID: ${result.event_id})`);
                // Invalidate calendar to refetch with new workout
                queryClient.invalidateQueries({ queryKey: queryKeys.weeklyCalendar() });
                queryClient.invalidateQueries({ queryKey: queryKeys.fitness() });
            } else {
                setError(result.error || "등록 실패");
            }
        },
        onError: (e: Error) => {
            setError(`등록 오류: ${e.message}`);
        },
    });

    const generatePlanMutation = useMutation({
        mutationFn: () => generateWeeklyPlan(session?.access_token || ''),
        onSuccess: (plan) => {
            // Update cache with new plan
            queryClient.setQueryData(queryKeys.weeklyPlan(weekStartDate), plan);
            setSuccess("✅ 주간 워크아웃 계획이 생성되었습니다!");
            // Invalidate related caches
            queryClient.invalidateQueries({ queryKey: queryKeys.weeklyCalendar() });
            queryClient.invalidateQueries({ queryKey: queryKeys.fitness() });
        },
        onError: (e: Error) => {
            const errorMsg = e.message;
            if (errorMsg.includes('rate_limit') || errorMsg.includes('429')) {
                setError(`⏱️ API 사용량 한도 도달. 잠시 후 다시 시도해주세요.`);
            } else {
                setError(`주간 계획 생성 실패: ${errorMsg}`);
            }
        },
    });

    const deletePlanMutation = useMutation({
        mutationFn: (planId: string) =>
            deleteWeeklyPlan(session?.access_token || '', planId),
        onSuccess: () => {
            // Remove from cache
            queryClient.setQueryData(queryKeys.weeklyPlan(weekStartDate), null);
            setSuccess("주간 계획이 삭제되었습니다.");
            // Invalidate calendar
            queryClient.invalidateQueries({ queryKey: queryKeys.weeklyCalendar() });
        },
        onError: (e: Error) => {
            setError(`삭제 실패: ${e.message}`);
        },
    });

    const registerPlanAllMutation = useMutation({
        mutationFn: (planId: string) =>
            registerWeeklyPlanToIntervals(session?.access_token || '', planId),
        onSuccess: (result) => {
            setSuccess(`${result.registered}개의 워크아웃이 Intervals.icu에 등록되었습니다.`);
            if (result.failed > 0) {
                setError(`${result.failed}개의 워크아웃 등록 실패`);
            }
            // Invalidate calendar to show registered workouts
            queryClient.invalidateQueries({ queryKey: queryKeys.weeklyCalendar() });
            queryClient.invalidateQueries({ queryKey: queryKeys.fitness() });
        },
        onError: (e: Error) => {
            setError(`등록 실패: ${e.message}`);
        },
    });

    // Actions
    const handleOnboardingComplete = useCallback(() => {
        // Invalidate API configured check to refetch
        queryClient.invalidateQueries({ queryKey: queryKeys.apiConfigured() });
    }, [queryClient]);

    const handleGenerate = useCallback(async (request: WorkoutGenerateRequest) => {
        setIsLoading(true);
        setError(null);
        setSuccess(null);
        setWorkout(null);

        try {
            await generateMutation.mutateAsync(request);
        } finally {
            setIsLoading(false);
        }
    }, [generateMutation]);

    const handleRegister = useCallback(async () => {
        if (!workout) return;

        setIsRegistering(true);
        setError(null);

        try {
            const today = new Date().toISOString().split("T")[0];
            await registerMutation.mutateAsync({
                target_date: today,
                name: workout.name,
                workout_text: workout.workout_text,
                duration_minutes: workout.estimated_duration_minutes,
                estimated_tss: workout.estimated_tss,
                design_goal: workout.design_goal,
                workout_type: workout.workout_type,
                force: true,
                steps: workout.steps,
            });
        } finally {
            setIsRegistering(false);
        }
    }, [workout, registerMutation]);

    const handleSelectDate = useCallback(async (date: string) => {
        setIsLoading(true);
        setError(null);
        setSuccess(null);
        setWorkout(null);

        try {
            const result = await fetchTodaysWorkout(session?.access_token || '', date);
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
        if (generatePlanMutation.isPending) return;

        setError(null);
        setSuccess(null);
        await generatePlanMutation.mutateAsync();
    }, [generatePlanMutation]);

    const handleDeleteWeeklyPlan = useCallback(async (planId: string) => {
        await deletePlanMutation.mutateAsync(planId);
    }, [deletePlanMutation]);

    const handleRegisterWeeklyPlanAll = useCallback(async (planId: string) => {
        setError(null);
        setSuccess(null);
        await registerPlanAllMutation.mutateAsync(planId);
    }, [registerPlanAllMutation]);

    const handleWeekNavigation = useCallback((direction: 'prev' | 'next') => {
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
        isGeneratingPlan: generatePlanMutation.isPending,
        isRegisteringPlanAll: registerPlanAllMutation.isPending,
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
