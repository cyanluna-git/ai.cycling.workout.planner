/**
 * WeeklyProgressSummary — TSS + Training Days progress display
 *
 * Desktop (md+): Two WeeklyProgressRing side by side
 *   - Ring 1: TSS progress (cyan)
 *   - Ring 2: Training days (amber)
 * Mobile (<md): Two slim progress bars stacked
 *
 * Placed inside WeeklyCalendarCard CardHeader.
 */

import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Skeleton } from "@/components/ui/skeleton";
import { WeeklyProgressRing } from "@/components/WeeklyProgressRing";

interface WeeklyProgressSummaryProps {
    tssAccumulated: number;
    tssTarget: number;
    trainingDaysCompleted: number;
    trainingDaysTarget: number;
    isLoading: boolean;
}

function ProgressBarSlim({
    value,
    max,
    color,
    label,
}: {
    value: number;
    max: number;
    color: string;
    label: string;
}) {
    const percentage = max > 0 ? Math.min((value / max) * 100, 100) : 0;
    const [animatedWidth, setAnimatedWidth] = useState(0);

    useEffect(() => {
        const timer = setTimeout(() => {
            setAnimatedWidth(percentage);
        }, 100);
        return () => {
            clearTimeout(timer);
            setAnimatedWidth(0);
        };
    }, [percentage]);

    return (
        <div className="flex items-center gap-2 w-full">
            <span className="text-[10px] text-muted-foreground whitespace-nowrap min-w-[70px]">
                {label}
            </span>
            <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                <div
                    className="h-full rounded-full transition-all duration-700 ease-out"
                    style={{
                        width: `${animatedWidth}%`,
                        backgroundColor: color,
                    }}
                />
            </div>
        </div>
    );
}

export function WeeklyProgressSummary({
    tssAccumulated,
    tssTarget,
    trainingDaysCompleted,
    trainingDaysTarget,
    isLoading,
}: WeeklyProgressSummaryProps) {
    const { t } = useTranslation();

    if (isLoading) {
        return (
            <div className="flex items-center gap-3">
                <Skeleton className="h-8 w-8 rounded-full" />
                <Skeleton className="h-8 w-8 rounded-full" />
            </div>
        );
    }

    const tssLabel = t("calendar.tssProgress", {
        accumulated: tssAccumulated,
        target: tssTarget || "-",
    });

    const trainingLabel = t("calendar.trainingDays", {
        completed: trainingDaysCompleted,
        target: trainingDaysTarget,
    });

    return (
        <>
            {/* Desktop: Two rings side by side */}
            <div className="hidden md:flex items-center gap-3">
                <WeeklyProgressRing
                    value={tssAccumulated}
                    max={tssTarget}
                    size={56}
                    strokeWidth={4}
                    color="#06b6d4"
                    label={tssLabel}
                />
                <WeeklyProgressRing
                    value={trainingDaysCompleted}
                    max={trainingDaysTarget}
                    size={56}
                    strokeWidth={4}
                    color="#f59e0b"
                    label={trainingLabel}
                />
            </div>

            {/* Mobile: Two slim progress bars stacked */}
            <div className="flex md:hidden flex-col gap-1 w-full mt-1">
                <ProgressBarSlim
                    value={tssAccumulated}
                    max={tssTarget}
                    color="#06b6d4"
                    label={tssLabel}
                />
                <ProgressBarSlim
                    value={trainingDaysCompleted}
                    max={trainingDaysTarget}
                    color="#f59e0b"
                    label={trainingLabel}
                />
            </div>
        </>
    );
}
