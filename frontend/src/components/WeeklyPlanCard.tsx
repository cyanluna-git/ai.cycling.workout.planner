import { useTranslation } from 'react-i18next';
/**
 * Weekly Plan Card Component
 *
 * Displays weekly workout plan with vertical list and power profile charts
 */

import { useState, memo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Sunrise, Sunset, Moon, Calendar, Loader2, RefreshCw, Trash2 } from "lucide-react";
import { getWorkoutTypeIcon, getStatusIcon } from "@/lib/icon-maps";
import { WorkoutThumbnailChart } from "@/components/WorkoutThumbnailChart";
import { WorkoutDetailModal } from "@/components/WorkoutDetailModal";
import type { WeeklyPlan, DailyWorkout } from "@/lib/api";
import { WeeklyPlanLoadingAnimation } from "@/components/CoachLoadingAnimation";

interface WeeklyPlanCardProps {
    plan: WeeklyPlan | null;
    isLoading: boolean;
    isGenerating: boolean;
    isRegisteringAll?: boolean;
    isSyncing?: boolean;
    currentWeekOffset: number;
    onGenerate: () => void;
    onDelete?: (planId: string) => void;
    onWeekNavigation?: (direction: 'prev' | 'next') => void;
    onRegisterAll?: (planId: string) => void;
    onSync?: (planId: string) => void;
}

// Workout type to color mapping
const typeColors: Record<string, string> = {
    Rest: "bg-gray-100 text-gray-600",
    Recovery: "bg-green-100 text-green-700",
    Endurance: "bg-blue-100 text-blue-700",
    Tempo: "bg-yellow-100 text-yellow-700",
    SweetSpot: "bg-orange-100 text-orange-700",
    Threshold: "bg-red-100 text-red-700",
    VO2max: "bg-purple-100 text-purple-700",
};

// Workout type icons are now from icon-maps.ts

function DailyWorkoutRow({
    workout,
    onClick,
}: {
    workout: DailyWorkout;
    onClick: () => void;
}) {
    const { t } = useTranslation();
    const workoutType = workout.planned_type || "Endurance";
    const colorClass = typeColors[workoutType] || typeColors.Endurance;
    const typeIcon = getWorkoutTypeIcon(workoutType, "h-3.5 w-3.5 inline");
    const isRest = workoutType === "Rest";

    // Session label for Norwegian-style double sessions
    const sessionIcon = workout.session === "AM" ? <Sunrise className="h-3 w-3 inline" /> : workout.session === "PM" ? <Sunset className="h-3 w-3 inline" /> : null;

    return (
        <div
            className={`flex items-center gap-2 px-2 py-2.5 min-h-[44px] rounded-lg ${colorClass} transition-all hover:scale-[1.01] cursor-pointer`}
            onClick={onClick}
            title={workout.planned_rationale}
        >
            {/* Left: Day info (compact) */}
            <div className="flex-shrink-0 w-12 text-center">
                <div className="text-[10px] font-medium opacity-70 leading-tight">
                    {workout.day_name}
                </div>
                <div className="text-base font-bold leading-tight">
                    {new Date(workout.workout_date).getDate()}
                </div>
            </div>

            {/* Middle: Workout info (compact, single line) */}
            <div className="flex-grow min-w-0">
                <div className="font-semibold text-xs truncate leading-tight flex items-center gap-1">
                    {sessionIcon}{typeIcon} {workout.planned_name || (isRest ? "Complete Rest" : "Workout")}
                </div>
                {!isRest && (
                    <div className="text-[10px] opacity-80 leading-tight">
                        {workout.planned_duration}{t("common.minutes")} • TSS {workout.planned_tss || 0}
                    </div>
                )}
                {isRest && (
                    <div className="text-[10px] opacity-60 leading-tight flex items-center gap-1"><Moon className="h-3 w-3 inline" /> Rest</div>
                )}
            </div>

            {/* Right: Chart thumbnail (compact) */}
            <div className="flex-shrink-0 w-28 h-8">
                {!isRest && workout.planned_steps && workout.planned_steps.length > 0 ? (
                    <WorkoutThumbnailChart steps={workout.planned_steps} height={32} />
                ) : null}
            </div>
        </div>
    );
}

export const WeeklyPlanCard = memo(function WeeklyPlanCard({
    plan,
    isLoading,
    isGenerating,
    isRegisteringAll,
    isSyncing,
    currentWeekOffset,
    onGenerate,
    onDelete,
    onWeekNavigation,
    onRegisterAll,
    onSync,
}: WeeklyPlanCardProps) {
    const { t } = useTranslation();
    const [showConfirmDelete, setShowConfirmDelete] = useState(false);
    const [selectedWorkout, setSelectedWorkout] = useState<DailyWorkout | null>(null);
    const [modalOpen, setModalOpen] = useState(false);

    // Handle workout click to open modal
    const handleWorkoutClick = (workout: DailyWorkout) => {
        if (workout.planned_steps && workout.planned_steps.length > 0) {
            setSelectedWorkout(workout);
            setModalOpen(true);
        }
    };

    // Get week label based on offset
    const getWeekLabel = () => {
        if (currentWeekOffset === 0) return t('weeklyPlan.thisWeek');
        if (currentWeekOffset === 1) return t('weeklyPlan.nextWeek');
        if (currentWeekOffset === -1) return t('weeklyPlan.lastWeek');
        if (currentWeekOffset > 1) return t('weeklyPlan.weeksLater', { count: currentWeekOffset });
        return t('weeklyPlan.weeksAgo', { count: Math.abs(currentWeekOffset) });
    };

    // Get next week's date range for display
    const getNextWeekRange = () => {
        const today = new Date();
        const daysUntilMonday = (8 - today.getDay()) % 7 || 7;
        const nextMonday = new Date(today);
        nextMonday.setDate(today.getDate() + daysUntilMonday);
        const nextSunday = new Date(nextMonday);
        nextSunday.setDate(nextMonday.getDate() + 6);

        const formatDate = (d: Date) => `${d.getMonth() + 1}/${d.getDate()}`;
        return `${formatDate(nextMonday)} ~ ${formatDate(nextSunday)}`;
    };

    if (isLoading || isGenerating) {
        return <WeeklyPlanLoadingAnimation />;
    }

    if (!plan) {
        return (
            <Card>
                <CardHeader>
                    {/* Week Navigation */}
                    {onWeekNavigation && (
                        <div className="flex items-center justify-center gap-4 mb-3">
                            <Button
                                variant="outline"
                                className="h-11 sm:h-9 transition-all active:scale-95"
                                onClick={() => onWeekNavigation('prev')}
                                disabled={isLoading}
                            >
                                {t("weeklyPlan.prevWeek")}
                            </Button>
                            <div className="text-sm font-medium px-4 py-2 bg-primary/10 rounded-md">
                                {getWeekLabel()}
                            </div>
                            <Button
                                variant="outline"
                                className="h-11 sm:h-9 transition-all active:scale-95"
                                onClick={() => onWeekNavigation('next')}
                                disabled={isLoading}
                            >
                                {t("weeklyPlan.nextWeekBtn")}
                            </Button>
                        </div>
                    )}

                    <CardTitle>{t("weeklyPlan.title")}</CardTitle>
                    <CardDescription>
                        {getWeekLabel()} ({getNextWeekRange()}) - {t("weeklyPlan.createPrompt")}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="py-12 text-center">
                        <div className="mb-4 flex justify-center"><Calendar className="h-12 w-12 text-primary" /></div>
                        <h3 className="text-xl font-bold mb-2">{t("weeklyPlan.emptyTitle")}</h3>
                        <p className="text-muted-foreground text-sm mb-6 max-w-md mx-auto">
                            {t("weeklyPlan.emptyDesc")}
                        </p>
                        {currentWeekOffset === 0 && (
                            <p className="text-xs text-blue-600 dark:text-blue-400 mb-4 max-w-md mx-auto">
                                {t("weeklyPlan.currentWeekHint")}
                            </p>
                        )}
                        <Button
                            onClick={onGenerate}
                            disabled={isGenerating}
                            className="w-full sm:w-auto"
                        >
                            {t("weeklyPlan.generatePlan")}
                        </Button>
                    </div>
                </CardContent>
            </Card>
        );
    }

    // Format date range for display
    const formatDateRange = () => {
        const start = new Date(plan.week_start);
        const end = new Date(plan.week_end);
        return `${start.getMonth() + 1}/${start.getDate()} ~ ${end.getMonth() + 1}/${end.getDate()}`;
    };

    // Training style display names
    const styleNames: Record<string, string> = {
        auto: t('settings.styleAuto'),
        polarized: t('settings.stylePolarized'),
        norwegian: t('settings.styleNorwegian'),
        sweetspot: t('settings.styleSweetspot'),
        threshold: t('settings.styleThreshold'),
        endurance: t('settings.styleEndurance'),
    };

    return (
        <Card>
            <CardHeader className="pb-3">
                {/* Week Navigation */}
                {onWeekNavigation && (
                    <div className="flex items-center justify-center gap-4 mb-3">
                        <Button
                            variant="outline"
                            className="h-11 sm:h-9 transition-all active:scale-95"
                            onClick={() => onWeekNavigation('prev')}
                            disabled={isLoading}
                        >
                            {t("weeklyPlan.prevWeek")}
                        </Button>
                        <div className="text-sm font-medium px-4 py-2 bg-primary/10 rounded-md">
                            {getWeekLabel()}
                        </div>
                        <Button
                            variant="outline"
                            className="h-11 sm:h-9 transition-all active:scale-95"
                            onClick={() => onWeekNavigation('next')}
                            disabled={isLoading}
                        >
                            {t("weeklyPlan.nextWeekBtn")}
                        </Button>
                    </div>
                )}

                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle>{t("weeklyPlan.title")}</CardTitle>
                        <CardDescription>
                            {formatDateRange()} • {styleNames[plan.training_style || "auto"]}
                        </CardDescription>
                    </div>
                    <div className="text-right">
                        <div className="text-sm font-medium">{t("weeklyPlan.totalTss")}</div>
                        <div className="text-2xl font-bold text-primary">
                            {plan.total_planned_tss || 0}
                        </div>
                        {plan.achievement_status && plan.achievement_status !== "no_target" && (
                            <div className={`text-xs mt-0.5 px-1.5 py-0.5 rounded-full inline-block ${
                                plan.achievement_status === "exceeded" ? "bg-yellow-100 text-yellow-700" :
                                plan.achievement_status === "achieved" ? "bg-green-100 text-green-700" :
                                plan.achievement_status === "partial" ? "bg-orange-100 text-orange-700" :
                                plan.achievement_status === "missed" ? "bg-red-100 text-red-700" :
                                "bg-blue-100 text-blue-700"
                            }`}>
                                {getStatusIcon(plan.achievement_status || "in_progress", "h-3 w-3 inline")}
                                {" "}{plan.achievement_pct != null ? `${plan.achievement_pct}%` : ""}
                            </div>
                        )}
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                {/* Vertical list - group by date for double sessions */}
                <div className="space-y-2 mb-4">
                    {(() => {
                        // Group workouts by date for Norwegian double sessions
                        const groupedByDate = new Map<string, DailyWorkout[]>();
                        plan.daily_workouts.forEach(workout => {
                            const date = workout.workout_date;
                            if (!groupedByDate.has(date)) {
                                groupedByDate.set(date, []);
                            }
                            groupedByDate.get(date)!.push(workout);
                        });

                        // Sort workouts within each group (AM before PM)
                        groupedByDate.forEach(workouts => {
                            workouts.sort((a, b) => {
                                if (a.session === "AM") return -1;
                                if (b.session === "AM") return 1;
                                return 0;
                            });
                        });

                        return Array.from(groupedByDate.entries()).map(([date, workouts]) => (
                            <div key={date}>
                                {workouts.length > 1 ? (
                                    // Double session (Norwegian style) - group with border
                                    <div className="border-l-4 border-purple-400 pl-2 space-y-1">
                                        {workouts.map((workout, idx) => (
                                            <DailyWorkoutRow
                                                key={`${date}-${idx}`}
                                                workout={workout}
                                                onClick={() => handleWorkoutClick(workout)}
                                            />
                                        ))}
                                    </div>
                                ) : (
                                    // Single session
                                    <DailyWorkoutRow
                                        workout={workouts[0]}
                                        onClick={() => handleWorkoutClick(workouts[0])}
                                    />
                                )}
                            </div>
                        ));
                    })()}
                </div>

                {/* Actions */}
                <div className="flex flex-wrap gap-2 justify-end pt-4 mt-4 border-t">
                    <Button
                        variant="outline"
                        className="h-11 sm:h-9 transition-all active:scale-95"
                        onClick={onGenerate}
                        disabled={isGenerating}
                    >
                        {isGenerating ? (<><Loader2 className="h-4 w-4 animate-spin" />{t("common.generating")}</> ) : t("weeklyPlan.regenerate")}
                    </Button>
                    {onSync && (
                        <Button
                            variant="outline"
                            className="h-11 sm:h-9 transition-all active:scale-95"
                            onClick={() => onSync(plan.id)}
                            disabled={isSyncing}
                        >
                            {isSyncing ? t("weeklyPlan.syncing") : <><RefreshCw className="h-4 w-4" /> Sync</>}
                        </Button>
                    )}
                    {onRegisterAll && (
                        <Button
                            variant="default"
                            className="h-11 sm:h-9 transition-all active:scale-95"
                            onClick={() => onRegisterAll(plan.id)}
                            disabled={isRegisteringAll}
                        >
                            {isRegisteringAll ? t("common.registering") : t("weeklyPlan.registerAll")}
                        </Button>
                    )}
                    {onDelete && (
                        <>
                            {showConfirmDelete ? (
                                <div className="flex gap-1">
                                    <Button
                                        variant="destructive"
                                        className="h-11 sm:h-9 transition-all active:scale-95"
                                        onClick={() => {
                                            onDelete(plan.id);
                                            setShowConfirmDelete(false);
                                        }}
                                    >{t("common.confirm")}</Button>
                                    <Button
                                        variant="ghost"
                                        className="h-11 sm:h-9 transition-all active:scale-95"
                                        onClick={() => setShowConfirmDelete(false)}
                                    >{t("common.cancel")}</Button>
                                </div>
                            ) : (
                                <Button
                                    variant="ghost"
                                    className="h-11 sm:h-9 transition-all active:scale-95"
                                    onClick={() => setShowConfirmDelete(true)}
                                ><Trash2 className="h-4 w-4" /> {t("common.delete")}</Button>
                            )}
                        </>
                    )}
                </div>
            </CardContent>

            {/* Modal for workout details */}
            <WorkoutDetailModal
                workout={selectedWorkout}
                open={modalOpen}
                onOpenChange={setModalOpen}
            />
        </Card>
    );
});
