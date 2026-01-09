/**
 * Weekly Plan Card Component
 * 
 * Displays weekly workout plan with 7-day view and actions
 */

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { WeeklyPlan, DailyWorkout } from "@/lib/api";

interface WeeklyPlanCardProps {
    plan: WeeklyPlan | null;
    isLoading: boolean;
    isGenerating: boolean;
    onGenerate: () => void;
    onDelete?: (planId: string) => void;
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

function DailyWorkoutCard({ workout }: { workout: DailyWorkout }) {
    const workoutType = workout.planned_type || "Endurance";
    const colorClass = typeColors[workoutType] || typeColors.Endurance;
    const emoji = typeEmoji[workoutType] || "🚴";
    const isRest = workoutType === "Rest";

    return (
        <div
            className={`rounded-lg p-3 ${colorClass} transition-all hover:scale-[1.02]`}
            title={workout.planned_rationale}
        >
            <div className="text-xs font-medium opacity-70">{workout.day_name}</div>
            <div className="font-semibold text-sm mt-1 truncate">
                {emoji} {workout.planned_name || (isRest ? "Rest Day" : "Workout")}
            </div>
            {!isRest && (
                <div className="text-xs mt-1 opacity-80">
                    {workout.planned_duration}분 • TSS {workout.planned_tss || 0}
                </div>
            )}
            {workout.status === "completed" && (
                <div className="text-xs mt-1 text-green-600 font-medium">✅ 완료</div>
            )}
            {workout.status === "skipped" && (
                <div className="text-xs mt-1 text-gray-500 font-medium">⏭️ 건너뜀</div>
            )}
            {workout.status === "regenerated" && (
                <div className="text-xs mt-1 text-blue-600 font-medium">🔄 재생성됨</div>
            )}
        </div>
    );
}

export function WeeklyPlanCard({
    plan,
    isLoading,
    isGenerating,
    onGenerate,
    onDelete,
}: WeeklyPlanCardProps) {
    const [showConfirmDelete, setShowConfirmDelete] = useState(false);

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
                    <CardTitle>📅 주간 워크아웃 계획</CardTitle>
                    <CardDescription>
                        다음 주 ({getNextWeekRange()}) 워크아웃 계획을 생성하세요
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
                {/* 7-day grid */}
                <div className="grid grid-cols-7 gap-2 mb-4">
                    {plan.daily_workouts.map((workout, index) => (
                        <DailyWorkoutCard key={index} workout={workout} />
                    ))}
                </div>

                {/* Actions */}
                <div className="flex flex-wrap gap-2 justify-end pt-2 border-t">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={onGenerate}
                        disabled={isGenerating}
                    >
                        {isGenerating ? "생성 중..." : "🔄 재생성"}
                    </Button>
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
        </Card>
    );
}
