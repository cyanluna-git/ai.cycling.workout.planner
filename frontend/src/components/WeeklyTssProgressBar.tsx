/**
 * Weekly TSS Progress Bar Component
 *
 * Displays weekly TSS progress as:
 * - Mobile: slim sticky bar at top (md:hidden)
 * - Desktop: card above the dashboard grid (hidden md:block)
 */

import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Trophy } from "lucide-react";

interface TssProgressData {
    target: number;
    accumulated: number;
    remaining: number;
    daysRemaining: number;
    achievable: boolean;
    warning?: string;
}

interface WeeklyTssProgressBarProps {
    tssProgress: TssProgressData | null;
    isLoading: boolean;
}

function TssProgressBarSkeleton({ className }: { className?: string }) {
    return (
        <div className={className}>
            <div className="flex items-center justify-between mb-1">
                <Skeleton className="h-3 w-24" />
                <Skeleton className="h-3 w-10" />
            </div>
            <Skeleton className="h-2.5 w-full rounded-full" />
        </div>
    );
}

export function WeeklyTssProgressBar({ tssProgress, isLoading }: WeeklyTssProgressBarProps) {
    const { t } = useTranslation();
    const [animatedWidth, setAnimatedWidth] = useState(0);

    const percentage = tssProgress && tssProgress.target > 0
        ? Math.round((tssProgress.accumulated / tssProgress.target) * 100)
        : 0;

    const cappedPercentage = Math.min(percentage, 100);
    const isAchieved = percentage >= 100;

    // Mount animation: 0 -> actual value after short delay
    useEffect(() => {
        if (!tssProgress || tssProgress.target <= 0) {
            setAnimatedWidth(0);
            return;
        }
        setAnimatedWidth(0);
        const timer = setTimeout(() => {
            setAnimatedWidth(cappedPercentage);
        }, 100);
        return () => clearTimeout(timer);
    }, [cappedPercentage, tssProgress]);

    // Loading skeleton
    if (isLoading) {
        return (
            <>
                {/* Mobile skeleton */}
                <div className="md:hidden sticky top-0 z-40 bg-background/95 backdrop-blur-sm border-b px-3 py-2">
                    <TssProgressBarSkeleton />
                </div>
                {/* Desktop skeleton */}
                <Card className="hidden md:block mb-4">
                    <CardContent className="py-3">
                        <TssProgressBarSkeleton />
                    </CardContent>
                </Card>
            </>
        );
    }

    // No data or zero target: hide completely
    if (!tssProgress || tssProgress.target <= 0) {
        return null;
    }

    const gradientClass = isAchieved
        ? "bg-gradient-to-r from-green-400 to-emerald-500"
        : "bg-gradient-to-r from-cyan-500 to-violet-500";

    const celebrationMessage = percentage > 100
        ? t("weeklyPlan.goalExceeded")
        : t("weeklyPlan.goalAchieved");

    const progressLabel = t("weeklyPlan.tssProgress", {
        accumulated: tssProgress.accumulated,
        target: tssProgress.target,
    });

    return (
        <>
            {/* Mobile: slim sticky bar */}
            <div className="md:hidden sticky top-0 z-40 bg-background/95 backdrop-blur-sm border-b px-3 py-2">
                <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-medium text-foreground/80">
                        {progressLabel}
                    </span>
                    <span className={`font-semibold ${isAchieved ? "text-green-600" : "text-foreground/60"}`}>
                        {percentage}%
                    </span>
                </div>
                <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                    <div
                        className={`h-full rounded-full transition-all duration-700 ease-out ${gradientClass}`}
                        style={{ width: `${animatedWidth}%` }}
                    />
                </div>
                {isAchieved && (
                    <div className="flex items-center gap-1 mt-1 text-[10px] text-green-600 font-medium">
                        <Trophy className="h-3 w-3" />
                        {celebrationMessage}
                    </div>
                )}
            </div>

            {/* Desktop: card */}
            <Card className="hidden md:block mb-4">
                <CardContent className="py-3">
                    <div className="flex items-center justify-between text-sm mb-1.5">
                        <span className="font-medium">
                            {t("weeklyPlan.weeklyProgress")}
                        </span>
                        <div className="flex items-center gap-3">
                            <span className="text-muted-foreground">
                                {progressLabel}
                            </span>
                            <span className={`font-semibold ${isAchieved ? "text-green-600" : "text-foreground"}`}>
                                {percentage}%
                            </span>
                        </div>
                    </div>
                    <div className="w-full h-2.5 bg-muted rounded-full overflow-hidden">
                        <div
                            className={`h-full rounded-full transition-all duration-700 ease-out ${gradientClass}`}
                            style={{ width: `${animatedWidth}%` }}
                        />
                    </div>
                    {isAchieved && (
                        <div className="flex items-center gap-1.5 mt-2 text-xs text-green-600 font-medium">
                            <Trophy className="h-3.5 w-3.5" />
                            {celebrationMessage}
                        </div>
                    )}
                    {!isAchieved && tssProgress.warning && (() => {
                        try {
                            const w = JSON.parse(tssProgress.warning);
                            return (
                                <div className="mt-2 p-2 bg-red-100 text-red-700 rounded text-xs">
                                    {t("weeklyPlan.tssWarningUnachievable", {
                                        days: w.days, target: w.target,
                                        accumulated: w.accumulated, pct: w.pct,
                                    })}
                                </div>
                            );
                        } catch {
                            return (
                                <div className="mt-2 p-2 bg-red-100 text-red-700 rounded text-xs">
                                    {tssProgress.warning}
                                </div>
                            );
                        }
                    })()}
                </CardContent>
            </Card>
        </>
    );
}
