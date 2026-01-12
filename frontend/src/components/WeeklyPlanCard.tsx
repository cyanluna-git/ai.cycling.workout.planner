/**
 * Weekly Plan Card Component
 *
 * Displays weekly workout plan with vertical list and power profile charts
 */

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { WorkoutThumbnailChart } from "@/components/WorkoutThumbnailChart";
import { WorkoutDetailModal } from "@/components/WorkoutDetailModal";
import type { WeeklyPlan, DailyWorkout } from "@/lib/api";

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

// Workout type to emoji mapping
const typeEmoji: Record<string, string> = {
    Rest: "😴",
    Recovery: "🌱",
    Endurance: "🚴",
    Tempo: "💪",
    SweetSpot: "🍯",
    Threshold: "🔥",
    VO2max: "⚡",
};

function DailyWorkoutRow({
    workout,
    onClick,
}: {
    workout: DailyWorkout;
    onClick: () => void;
}) {
    const workoutType = workout.planned_type || "Endurance";
    const colorClass = typeColors[workoutType] || typeColors.Endurance;
    const emoji = typeEmoji[workoutType] || "🚴";
    const isRest = workoutType === "Rest";

    // Session label for Norwegian-style double sessions
    const sessionLabel = workout.session === "AM" ? "🌅" : workout.session === "PM" ? "🌆" : "";

    return (
        <div
            className={`flex items-center gap-2 px-2 py-1.5 rounded-lg ${colorClass} transition-all hover:scale-[1.01] cursor-pointer`}
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
                <div className="font-semibold text-xs truncate leading-tight">
                    {sessionLabel}{emoji} {workout.planned_name || (isRest ? "Complete Rest" : "Workout")}
                </div>
                {!isRest && (
                    <div className="text-[10px] opacity-80 leading-tight">
                        {workout.planned_duration}분 • TSS {workout.planned_tss || 0}
                    </div>
                )}
                {isRest && (
                    <div className="text-[10px] opacity-60 leading-tight">😴 Rest</div>
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

export function WeeklyPlanCard({
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
        if (currentWeekOffset === 0) return "이번 주";
        if (currentWeekOffset === 1) return "다음 주";
        if (currentWeekOffset === -1) return "지난 주";
        if (currentWeekOffset > 1) return `${currentWeekOffset}주 후`;
        return `${Math.abs(currentWeekOffset)}주 전`;
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

    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>📅 주간 워크아웃 계획</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center py-8">
                        <div className="animate-spin h-6 w-6 border-2 border-primary border-t-transparent rounded-full"></div>
                        <span className="ml-2 text-muted-foreground">로딩 중...</span>
                    </div>
                </CardContent>
            </Card>
        );
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
                                size="sm"
                                onClick={() => onWeekNavigation('prev')}
                                disabled={isLoading}
                            >
                                ← 지난 주
                            </Button>
                            <div className="text-sm font-medium px-4 py-2 bg-primary/10 rounded-md">
                                {getWeekLabel()}
                            </div>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => onWeekNavigation('next')}
                                disabled={isLoading}
                            >
                                다음 주 →
                            </Button>
                        </div>
                    )}

                    <CardTitle>📅 주간 워크아웃 계획</CardTitle>
                    <CardDescription>
                        {getWeekLabel()} ({getNextWeekRange()}) 워크아웃 계획을 생성하세요
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="text-center py-6">
                        <p className="text-muted-foreground mb-4">
                            아직 생성된 주간 계획이 없습니다.
                        </p>
                        <Button
                            onClick={onGenerate}
                            disabled={isGenerating}
                            className="w-full sm:w-auto"
                        >
                            {isGenerating ? (
                                <>
                                    <span className="animate-spin mr-2">⏳</span>
                                    생성 중...
                                </>
                            ) : (
                                <>🗓️ 주간 계획 생성</>
                            )}
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
        auto: "자동 (TSB 기반)",
        polarized: "양극화 (80/20)",
        norwegian: "노르웨이식 (역치)",
        sweetspot: "스윗스팟",
        threshold: "역치 중심",
        endurance: "지구력",
    };

    return (
        <Card>
            <CardHeader className="pb-3">
                {/* Week Navigation */}
                {onWeekNavigation && (
                    <div className="flex items-center justify-center gap-4 mb-3">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onWeekNavigation('prev')}
                            disabled={isLoading}
                        >
                            ← 지난 주
                        </Button>
                        <div className="text-sm font-medium px-4 py-2 bg-primary/10 rounded-md">
                            {getWeekLabel()}
                        </div>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onWeekNavigation('next')}
                            disabled={isLoading}
                        >
                            다음 주 →
                        </Button>
                    </div>
                )}

                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle>📅 주간 워크아웃 계획</CardTitle>
                        <CardDescription>
                            {formatDateRange()} • {styleNames[plan.training_style || "auto"]}
                        </CardDescription>
                    </div>
                    <div className="text-right">
                        <div className="text-sm font-medium">총 TSS</div>
                        <div className="text-2xl font-bold text-primary">
                            {plan.total_planned_tss || 0}
                        </div>
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
                        size="sm"
                        onClick={onGenerate}
                        disabled={isGenerating}
                    >
                        {isGenerating ? "생성 중..." : "🔄 재생성"}
                    </Button>
                    {onSync && (
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onSync(plan.id)}
                            disabled={isSyncing}
                        >
                            {isSyncing ? "동기화 중..." : "🔃 Sync"}
                        </Button>
                    )}
                    {onRegisterAll && (
                        <Button
                            variant="default"
                            size="sm"
                            onClick={() => onRegisterAll(plan.id)}
                            disabled={isRegisteringAll}
                        >
                            {isRegisteringAll ? "등록 중..." : "📤 Intervals.icu 등록"}
                        </Button>
                    )}
                    {onDelete && (
                        <>
                            {showConfirmDelete ? (
                                <div className="flex gap-1">
                                    <Button
                                        variant="destructive"
                                        size="sm"
                                        onClick={() => {
                                            onDelete(plan.id);
                                            setShowConfirmDelete(false);
                                        }}
                                    >
                                        확인
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => setShowConfirmDelete(false)}
                                    >
                                        취소
                                    </Button>
                                </div>
                            ) : (
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setShowConfirmDelete(true)}
                                >
                                    🗑️ 삭제
                                </Button>
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
}
