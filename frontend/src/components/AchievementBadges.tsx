import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Flame } from "lucide-react";
import { getStatusIcon } from "@/lib/icon-maps";
import type { AchievementsData } from '@/lib/api';

interface AchievementBadgesProps {
    data: AchievementsData | null;
    isLoading: boolean;
}

// Status icons are now from icon-maps.ts

const statusColors: Record<string, string> = {
    exceeded: 'bg-yellow-200',
    achieved: 'bg-green-200',
    partial: 'bg-orange-200',
    missed: 'bg-red-200',
    in_progress: 'bg-blue-200',
    no_target: 'bg-gray-200',
};

export function AchievementBadges({ data, isLoading }: AchievementBadgesProps) {
    const { t } = useTranslation();

    if (isLoading) {
        return (
            <Card>
                <CardContent className="p-4">
                    <div className="animate-pulse h-20 bg-gray-100 rounded" />
                </CardContent>
            </Card>
        );
    }

    if (!data) return null;

    return (
        <Card>
            <CardHeader className="pb-2 pt-3 px-4">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                    {data.current_streak > 0 && (
                        <Flame className="h-5 w-5 text-orange-500" />
                    )}
                    {data.current_streak > 0
                        ? t('achievements.streakLabel', { count: data.current_streak })
                        : t('achievements.noStreak')}
                </CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-3">
                {/* Stats row */}
                <div className="flex gap-4 text-xs text-gray-600 mb-3">
                    <span>{t('achievements.bestStreak', { count: data.best_streak })}</span>
                    <span>{t('achievements.totalAchieved', { count: data.total_achieved_weeks })}</span>
                </div>

                {/* Earned badges */}
                {data.earned_badges.length > 0 && (
                    <div className="mb-3">
                        <div className="text-xs font-medium text-gray-500 mb-1">
                            {t('achievements.earnedBadges')}
                        </div>
                        <div className="flex flex-wrap gap-1">
                            {data.earned_badges.map((badge) => (
                                <span
                                    key={badge.id}
                                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-yellow-50 text-xs"
                                    title={badge.name}
                                >
                                    {badge.icon} {badge.name}
                                </span>
                            ))}
                        </div>
                    </div>
                )}

                {/* Next badge */}
                {data.next_badge && (
                    <div className="text-xs text-gray-500">
                        {data.next_badge.icon} {t('achievements.nextBadge', { remaining: data.next_badge.remaining })}
                    </div>
                )}

                {/* Mini weekly history (last 12 weeks) */}
                {data.weekly_history.length > 0 && (
                    <div className="mt-3">
                        <div className="flex gap-0.5 justify-end">
                            {[...data.weekly_history].reverse().map((week, idx) => (
                                <div
                                    key={idx}
                                    className={`w-4 h-4 rounded-sm ${statusColors[week.achievement_status] || 'bg-gray-100'} flex items-center justify-center`}
                                    title={`${week.week_start}: ${week.achievement_pct}%`}
                                >
                                    <span className="flex items-center justify-center">
                                        {getStatusIcon(week.achievement_status, "h-2.5 w-2.5")}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
