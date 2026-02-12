import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { WeeklyCalendarData, WeeklyEvent } from "@/lib/api";
import { cleanWorkoutName } from "@/lib/workout-utils";

interface WeeklyCalendarCardProps {
    calendar: WeeklyCalendarData | null;
    isLoading: boolean;
    onSelectDate?: (date: string) => void;
}

// DAY_NAMES now from i18n

function getEventIcon(event: WeeklyEvent): string {
    const t = (event.workout_type || event.category).toLowerCase();

    let icon = "🚴";
    if (t.includes("run") || t.includes("walk")) icon = "🏃";
    if (t.includes("swim")) icon = "🏊";
    if (t.includes("weight") || t.includes("strength")) icon = "🏋️";

    return icon;
}

/**
 * Get workout type color/style - Clear distinction between Plan and Activity
 */
function getEventStyle(event: WeeklyEvent) {
    // Actual (completed) activities: Green theme with checkmark
    if (event.is_actual) {
        return {
            backgroundColor: '#dcfce7', // Light green background
            borderLeft: '3px solid #22c55e', // Green border
            color: '#166534', // Dark green text
        };
    }

    // Planned workouts: Blue theme
    return {
        backgroundColor: '#dbeafe', // Light blue background
        borderLeft: '3px dashed #3b82f6', // Blue dashed border (indicates planned)
        color: '#1e40af', // Dark blue text
    };
}

/**
 * Format date as "DD"
 */
function formatDate(dateStr: string): string {
    const d = new Date(dateStr);
    return `${d.getDate()}`;
}

/**
 * Check if date is today
 */
function isToday(dateStr: string): boolean {
    const today = new Date();
    const d = new Date(dateStr);
    return today.toDateString() === d.toDateString();
}

export function WeeklyCalendarCard({ calendar, isLoading, onSelectDate }: WeeklyCalendarCardProps) {
    const { t } = useTranslation();
    if (isLoading) {
        return (
            <Card>
                <CardHeader className="pb-2">
                    <CardTitle className="text-lg">{t('calendar.title')}</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="animate-pulse space-y-2">
                        <div className="h-16 bg-muted rounded"></div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (!calendar) return null;

    // Generate week days from week_start
    const weekStart = new Date(calendar.week_start);
    const days: { date: string; dayName: string; events: WeeklyEvent[] }[] = [];

    for (let i = 0; i < 7; i++) {
        const d = new Date(weekStart);
        d.setDate(weekStart.getDate() + i);
        const dateStr = d.toISOString().slice(0, 10);
        const dayEvents = calendar.events.filter(e => e.date === dateStr);

        // Separate into planned and actual
        const plannedEvents = dayEvents.filter(e => !e.is_actual);
        const actualEvents = dayEvents.filter(e => e.is_actual);

        // Show planned first (top), then actual (bottom)
        days.push({
            date: dateStr,
            dayName: (t('calendar.dayNames', { returnObjects: true }) as string[])[i],
            events: [...plannedEvents, ...actualEvents]
        });
    }

    return (
        <Card>
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{t('calendar.title')}</CardTitle>
                    <div className="flex gap-4 text-xs">
                        <div className="flex items-center gap-1.5 bg-blue-100 px-2 py-1 rounded">
                            <span className="w-2 h-2 border border-dashed border-blue-500 rounded-sm"></span>
                            <span className="text-blue-700">{t('calendar.planned')} {calendar.planned_tss}</span>
                        </div>
                        <div className="flex items-center gap-1.5 bg-green-100 px-2 py-1 rounded">
                            <span className="w-2 h-2 bg-green-500 rounded-sm"></span>
                            <span className="text-green-700">{t('calendar.completed')} {calendar.actual_tss}</span>
                        </div>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-7 gap-1">
                    {days.map((day) => (
                        <div
                            key={day.date}
                            onClick={() => onSelectDate?.(day.date)}
                            className={`text-center p-2 rounded-lg min-h-24 cursor-pointer transition-all hover:bg-muted/80 ${isToday(day.date) ? 'bg-primary/5 ring-2 ring-primary' : 'bg-muted/30'
                                }`}
                        >
                            <div className="text-xs text-muted-foreground mb-1">{day.dayName}</div>
                            <div className={`text-sm font-bold mb-2 ${isToday(day.date) ? 'text-primary' : ''}`}>
                                {formatDate(day.date)}
                            </div>

                            <div className="space-y-1">
                                {day.events.map((event) => (
                                    <div
                                        key={event.id}
                                        className="text-[10px] p-1.5 rounded text-left truncate leading-tight"
                                        style={getEventStyle(event)}
                                        title={`${event.name}\n${event.is_actual ? t('calendar.completedActivity') : t('calendar.plannedWorkout')}`}
                                    >
                                        <div className="flex items-center gap-1">
                                            {event.is_actual ? (
                                                <span className="text-green-600">✓</span>
                                            ) : (
                                                <span className="opacity-60">•</span>
                                            )}
                                            <span className="flex items-center gap-0.5">
                                                <span>{getEventIcon(event)}</span>
                                                <span className="truncate">
                                                    {cleanWorkoutName(event.name)}
                                                </span>
                                            </span>
                                        </div>
                                        {event.tss ? (
                                            <div className="mt-0.5 opacity-80 text-[9px] pl-3">
                                                TSS {event.tss}
                                                {event.duration_minutes ? ` • ${event.duration_minutes}m` : ''}
                                            </div>
                                        ) : null}
                                    </div>
                                ))}
                            </div>

                            {day.events.length === 0 && (
                                <div className="text-xs text-muted-foreground pt-4">-</div>
                            )}
                        </div>
                    ))}
                </div>

                {/* Legend */}
                <div className="flex justify-center gap-6 mt-3 pt-3 border-t text-xs text-muted-foreground">
                    <div className="flex items-center gap-1.5">
                        <span className="text-green-600">✓</span>
                        <span>{t('calendar.completedLegend')}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <span className="opacity-60">•</span>
                        <span>{t('calendar.plannedLegend')}</span>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
