/**
 * useDashboard Hook with React Query
 *
 * Optimized data fetching with:
 * - Automatic caching (2 hour stale time)
 * - Parallel requests for independent data
 * - Optimistic UI updates
 * - Background refetching
 */

import { useState, useCallback, useEffect } from "react";
import type { WorkoutStep } from "@/types/workout";
import i18n from '@/i18n/config';
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { queryKeys } from "@/lib/queryClient";
import { getCachedData, setCachedData } from "@/lib/queryCache";
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
    syncWeeklyPlanWithIntervals,
    fetchAchievements,
    type FitnessData,
    type GeneratedWorkout,
    type WorkoutGenerateRequest,
    type AchievementsData,
    type WeeklyCalendarData,
    type WeeklyPlan,
    type SyncResult,

    fetchTodayPlan,
} from "@/lib/api";

interface TssProgressData {
    target: number;
    accumulated: number;
    remaining: number;
    daysRemaining: number;
    achievable: boolean;
    warning?: string;
}

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
    isSyncingPlan: boolean;
    syncResult: SyncResult | null;
    isLoading: boolean;
    isRegistering: boolean;
    error: string | null;
    success: string | null;
    tssProgress: TssProgressData | null;
    achievements: AchievementsData | null;
    isLoadingAchievements: boolean;
}

interface DashboardActions {
    handleGenerate: (request: WorkoutGenerateRequest) => Promise<void>;
    handleRegister: () => Promise<void>;
    handleSelectDate: (date: string) => Promise<void>;
    handleOnboardingComplete: () => void;
    handleGenerateWeeklyPlan: () => Promise<void>;
    handleDeleteWeeklyPlan: (planId: string) => Promise<void>;
    handleRegisterWeeklyPlanAll: (planId: string) => Promise<void>;
    handleSyncWeeklyPlan: (planId: string) => Promise<void>;
    handleWeekNavigation: (direction: 'prev' | 'next') => void;
    clearMessages: () => void;
    clearSyncResult: () => void;
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
    const [isSyncingPlan, setIsSyncingPlan] = useState(false);
    const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // Helper function to get local date string (YYYY-MM-DD)
    const getLocalDateString = useCallback((date: Date = new Date()): string => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }, []);

    // Helper function to calculate Monday of a week with offset
    const getWeekStartDate = useCallback((offset: number): string => {
        const today = new Date();
        const dayOfWeek = today.getDay();
        const daysToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
        const monday = new Date(today);
        monday.setDate(today.getDate() + daysToMonday + (offset * 7));
        return getLocalDateString(monday);
    }, [getLocalDateString]);

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
        queryFn: async () => {
            const result = await fetchFitness(session?.access_token || '');
            setCachedData('fitness', result);
            return result;
        },
        enabled: !!session?.access_token,
        staleTime: 2 * 60 * 60 * 1000, // 2 hours
        placeholderData: () => getCachedData<FitnessData>('fitness'),
    });

    // Fetch weekly calendar (cached for 2 hours)
    const {
        data: weeklyCalendar = null,
        isLoading: isLoadingCalendar,
    } = useQuery({
        queryKey: queryKeys.weeklyCalendar(),
        queryFn: async () => {
            const result = await fetchWeeklyCalendar(session?.access_token || '');
            setCachedData('weeklyCalendar', result);
            return result;
        },
        enabled: !!session?.access_token,
        staleTime: 2 * 60 * 60 * 1000, // 2 hours
        placeholderData: () => getCachedData<WeeklyCalendarData>('weeklyCalendar'),
    });

    // Fetch weekly plan (cached per week)
    const weekStartDate = getWeekStartDate(currentWeekOffset);
    const {
        data: weeklyPlan = null,
        isLoading: isLoadingPlan,
    } = useQuery({
        queryKey: queryKeys.weeklyPlan(weekStartDate),
        queryFn: async () => {
            const result = await fetchWeeklyPlan(session?.access_token || '', weekStartDate);
            setCachedData(`weeklyPlan-${weekStartDate}`, result);
            return result;
        },
        enabled: !!session?.access_token,
        staleTime: 2 * 60 * 60 * 1000, // 2 hours
        placeholderData: () => getCachedData<WeeklyPlan>(`weeklyPlan-${weekStartDate}`),
    });

    // Fetch today's workout (initially)
    const { data: todayWorkoutData } = useQuery({
        queryKey: queryKeys.todayWorkout(),
        queryFn: () => fetchTodaysWorkout(session?.access_token || ''),
        enabled: !!session?.access_token,
        staleTime: 1 * 60 * 60 * 1000, // 1 hour
    });

    // Fetch today's plan (for TSS tracking)
    const { data: todayPlanData } = useQuery({
        queryKey: [...queryKeys.weeklyPlan("today-plan")],
        queryFn: () => fetchTodayPlan(session?.access_token || ''),
        enabled: !!session?.access_token,
        staleTime: 30 * 60 * 1000, // 30 minutes
    });

    // Build TSS progress from todayPlanData
    const tssProgress: TssProgressData | null = todayPlanData?.weekly_tss_target
        ? {
            target: todayPlanData.weekly_tss_target,
            accumulated: todayPlanData.weekly_tss_accumulated || 0,
            remaining: todayPlanData.weekly_tss_remaining || 0,
            daysRemaining: todayPlanData.days_remaining_in_week || 0,
            achievable: todayPlanData.target_achievable !== false,
            warning: todayPlanData.achievement_warning || undefined,
        }
        : null;

    // Mutations
    const generateMutation = useMutation({
        mutationFn: (request: WorkoutGenerateRequest) =>
            generateWorkout(request, session?.access_token || ''),
        onSuccess: (result) => {
            if (result.success && result.workout) {
                setWorkout(result.workout);
                setError(null);
            } else {
                setError(result.error || i18n.t("workout.generateFailed"));
            }
        },
        onError: (e: Error) => {
            setError(i18n.t("workout.generateError", { message: e.message }));
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
            steps?: WorkoutStep[];
        }) => createWorkout(data, session?.access_token || ''),
        onSuccess: (result) => {
            if (result.success) {
                setSuccess(i18n.t("workout.registerSuccess", { eventId: result.event_id }));
                // Invalidate calendar to refetch with new workout
                queryClient.invalidateQueries({ queryKey: queryKeys.weeklyCalendar() });
                queryClient.invalidateQueries({ queryKey: queryKeys.fitness() });
            } else {
                setError(result.error || i18n.t("workout.registerFailed"));
            }
        },
        onError: (e: Error) => {
            setError(i18n.t("workout.registerError", { message: e.message }));
        },
    });

    const generatePlanMutation = useMutation({
        mutationFn: () => generateWeeklyPlan(session?.access_token || '', undefined, todayPlanData?.weekly_tss_target || undefined),
        onSuccess: (plan) => {
            // Update cache with new plan
            queryClient.setQueryData(queryKeys.weeklyPlan(weekStartDate), plan);
            setSuccess(i18n.t("weeklyPlan.generateSuccess"));
            // Invalidate related caches
            queryClient.invalidateQueries({ queryKey: queryKeys.weeklyCalendar() });
            queryClient.invalidateQueries({ queryKey: queryKeys.fitness() });
        },
        onError: (e: Error) => {
            const errorMsg = e.message;
            if (errorMsg.includes('rate_limit') || errorMsg.includes('429')) {
                setError(i18n.t("weeklyPlan.generateRateLimit"));
            } else {
                setError(i18n.t("weeklyPlan.generateFailed", { message: errorMsg }));
            }
        },
    });

    const deletePlanMutation = useMutation({
        mutationFn: (planId: string) =>
            deleteWeeklyPlan(session?.access_token || '', planId),
        onSuccess: () => {
            // Remove from cache
            queryClient.setQueryData(queryKeys.weeklyPlan(weekStartDate), null);
            setSuccess(i18n.t("weeklyPlan.deleted"));
            // Invalidate calendar
            queryClient.invalidateQueries({ queryKey: queryKeys.weeklyCalendar() });
        },
        onError: (e: Error) => {
            setError(i18n.t("weeklyPlan.deleteFailed", { message: e.message }));
        },
    });

    const registerPlanAllMutation = useMutation({
        mutationFn: (planId: string) =>
            registerWeeklyPlanToIntervals(session?.access_token || '', planId),
        onSuccess: (result) => {
            setSuccess(i18n.t("weeklyPlan.registerResult", { registered: result.registered }));
            if (result.failed > 0) {
                setError(i18n.t("weeklyPlan.registerPartialFail", { failed: result.failed }));
            }
            // Invalidate calendar to show registered workouts
            queryClient.invalidateQueries({ queryKey: queryKeys.weeklyCalendar() });
            queryClient.invalidateQueries({ queryKey: queryKeys.fitness() });
        },
        onError: (e: Error) => {
            setError(i18n.t("weeklyPlan.registerFailed", { message: e.message }));
        },
    });

    // Handle today's workout data when it arrives (only if no workout is set)
    useEffect(() => {
        if (!workout && todayWorkoutData && todayWorkoutData.success && todayWorkoutData.workout) {
            setWorkout(todayWorkoutData.workout);
            setSuccess(i18n.t("workout.loadedWorkout"));
        }
    }, [todayWorkoutData, workout]);

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
            const today = getLocalDateString();
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
    }, [workout, registerMutation, getLocalDateString]);

    const handleSelectDate = useCallback(async (date: string) => {
        setIsLoading(true);
        setError(null);
        setSuccess(null);
        setWorkout(null);

        try {
            const result = await fetchTodaysWorkout(session?.access_token || '', date);
            if (result.success && result.workout) {
                setWorkout(result.workout);
                setSuccess(i18n.t("workout.loadedDateWorkout", { date }));
            } else {
                setError(i18n.t("workout.noSavedWorkout", { date }));
            }
        } catch (e) {
            setError(i18n.t("workout.loadFailed", { message: e instanceof Error ? e.message : String(e) }));
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

    const handleSyncWeeklyPlan = useCallback(async (planId: string) => {
        setIsSyncingPlan(true);
        setError(null);
        setSyncResult(null);
        try {
            const result = await syncWeeklyPlanWithIntervals(session?.access_token || '', planId);
            setSyncResult(result);
            if (result.success) {
                const hasChanges = result.changes.deleted.length > 0 ||
                    result.changes.moved.length > 0 ||
                    result.changes.modified.length > 0;
                if (hasChanges) {
                    // Invalidate to refresh data after sync
                    queryClient.invalidateQueries({ queryKey: queryKeys.weeklyPlan(weekStartDate) });
                }
                setSuccess(result.message);
            }
        } catch (e) {
            setError(i18n.t("weeklyPlan.syncFailed", { message: e instanceof Error ? e.message : String(e) }));
        } finally {
            setIsSyncingPlan(false);
        }
    }, [session, queryClient, weekStartDate]);

    const clearSyncResult = useCallback(() => {
        setSyncResult(null);
    }, []);

    // Achievements query
    const { data: achievements = null, isLoading: isLoadingAchievements } = useQuery<AchievementsData | null>({
        queryKey: ["achievements", session?.access_token],
        queryFn: async () => {
            if (!session?.access_token) return null;
            const result = await fetchAchievements(session.access_token);
            setCachedData('achievements', result);
            return result;
        },
        enabled: !!session?.access_token,
        staleTime: 1000 * 60 * 30, // 30 min
        placeholderData: () => getCachedData<AchievementsData>('achievements'),
    });

    return {
        // State
        isApiConfigured,
        fitness,
        workout,
        weeklyCalendar,
        weeklyPlan,
        achievements,
        isLoadingAchievements,
        currentWeekOffset,
        isLoadingCalendar,
        isLoadingPlan,
        isGeneratingPlan: generatePlanMutation.isPending,
        isRegisteringPlanAll: registerPlanAllMutation.isPending,
        isSyncingPlan,
        syncResult,
        isLoading,
        isRegistering,
        error,
        success,
        tssProgress,
        // Actions
        handleGenerate,
        handleRegister,
        handleSelectDate,
        handleOnboardingComplete,
        handleGenerateWeeklyPlan,
        handleDeleteWeeklyPlan,
        handleRegisterWeeklyPlanAll,
        handleSyncWeeklyPlan,
        handleWeekNavigation,
        clearSyncResult,
        clearMessages,
    };
}
