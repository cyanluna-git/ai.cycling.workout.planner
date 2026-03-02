import type { ReactNode } from "react";
import { useTranslation } from 'react-i18next';
import { Check } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getEventTypeIcon } from "@/lib/icon-maps";
import type { WeeklyCalendarData, WeeklyEvent } from "@/lib/api";
import { cleanWorkoutName } from "@/lib/workout-utils";

interface WeeklyCalendarCardProps {
    calendar: WeeklyCalendarData | null;
    isLoading: boolean;
    onSelectDate?: (date: string) => void;
}

// DAY_NAMES now from i18n

function getEventIconNode(event: WeeklyEvent): ReactNode {
    return getEventTypeIcon(
        { workout_type: event.workout_type ?? undefined, category: event.category },
        "h-3 w-3 inline",
    );
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
    const dayNamesShort = t('calendar.dayNames', { returnObjects: true }) as string[];
    const dayNamesFull = t('calendar.dayNamesFull', { returnObjects: true }) as string[];
    const days: { date: string; dayName: string; dayNameFull: string; events: WeeklyEvent[] }[] = [];

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
            dayName: dayNamesShort[i],
            dayNameFull: dayNamesFull[i],
            events: [...plannedEvents, ...actualEvents]
        });
    }

    return (
        <Card>
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{t('calendar.title')}</CardTitle>
                    <div className="flex flex-wrap gap-2 md:gap-4 text-xs">
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
                <div className="flex flex-col divide-y divide-border/40">
                    {days.map((day) => {
                        const rows: (WeeklyEvent | null)[] = day.events.length > 0
                            ? day.events
                            : [null]; // null = rest day row

                        return rows.map((event, idx) => (
                            <div
                                key={`${day.date}-${event?.id ?? 'rest'}`}
                                onClick={() => onSelectDate?.(day.date)}
                                className="flex items-center gap-2 py-1.5 px-1 cursor-pointer hover:bg-muted/30 transition-colors"
                            >
                                {/* Day name — only on first row, invisible on subsequent rows */}
                                <span
                                    className={`w-24 shrink-0 text-sm font-semibold ${
                                        idx === 0 && isToday(day.date)
                                            ? 'text-primary'
                                            : idx > 0
                                                ? 'invisible'
                                                : ''
                                    }`}
                                >
                                    {day.dayNameFull}
                                </span>

                                {/* Event or rest day */}
                                {event === null ? (
                                    <span className="text-xs text-muted-foreground">
                                        {t('calendar.restDay')}
                                    </span>
                                ) : (
                                    <div
                                        className="flex items-center gap-1.5 min-w-0 flex-1 rounded px-2 py-1 text-xs"
                                        style={getEventStyle(event)}
                                        title={`${event.name}\n${event.is_actual ? t('calendar.completedActivity') : t('calendar.plannedWorkout')}`}
                                    >
                                        {/* Badge */}
                                        {event.is_actual ? (
                                            <span className="shrink-0 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-green-200 text-green-800">
                                                {t('calendar.doneLabel')}
                                            </span>
                                        ) : (
                                            <span className="shrink-0 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-200 text-blue-800">
                                                {t('calendar.planLabel')}
                                            </span>
                                        )}
                                        {/* Icon */}
                                        <span className="shrink-0">{getEventIconNode(event)}</span>
                                        {/* Name — truncate */}
                                        <span className="truncate">{cleanWorkoutName(event.name)}</span>
                                        {/* TSS + duration inline */}
                                        {event.tss ? (
                                            <span className="shrink-0 text-[10px] opacity-70 ml-auto whitespace-nowrap">
                                                TSS {event.tss}
                                                {event.duration_minutes ? ` · ${event.duration_minutes}m` : ''}
                                            </span>
                                        ) : null}
                                    </div>
                                )}
                            </div>
                        ));
                    })}
                </div>

                {/* Legend */}
                <div className="flex flex-wrap justify-center gap-6 mt-3 pt-3 border-t text-xs text-muted-foreground">
                    <div className="flex items-center gap-1.5">
                        <Check className="h-3 w-3 text-green-600" />
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
