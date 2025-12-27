import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { WeeklyCalendarData, WeeklyEvent } from "@/lib/api";

interface WeeklyCalendarCardProps {
    calendar: WeeklyCalendarData | null;
    isLoading: boolean;
    onSelectDate?: (date: string) => void;
}

const DAY_NAMES = ['월', '화', '수', '목', '금', '토', '일'];

function getEventIcon(event: WeeklyEvent): string {
    const t = (event.workout_type || event.category).toLowerCase();

    // Activity Status
    const isActual = event.is_actual;
    const isIndoor = event.is_indoor;

    let icon = "🚴";
    if (t.includes("run")) icon = "🏃";
    if (t.includes("swim")) icon = "🏊";
    if (t.includes("weight") || t.includes("strength")) icon = "🏋️";

    if (isActual) {
        return isIndoor ? `${icon}🏠` : `${icon}🌲`;
    }
    return icon;
}

/**
 * Get workout type color/style
 */
function getEventStyle(event: WeeklyEvent) {
    const t = (event.workout_type || event.category).toLowerCase();
    let color = '#8b5cf6'; // Default purple

    if (t.includes('ride') || t.includes('virtual')) color = '#0ea5e9'; // Blue
    if (t.includes('run')) color = '#f97316'; // Orange
    if (t.includes('swim')) color = '#22c55e'; // Green

    // Actual vs Planned styling
    if (event.is_actual) {
        return {
            backgroundColor: `${color}30`, // Darker background for completed
            borderLeft: `4px solid ${color}`,
            color: 'inherit',
            fontWeight: 'bold' // Bold for completed
        };
    } else {
        return {
            backgroundColor: `${color}10`, // Lighter for planned
            borderLeft: `2px solid ${color}80`, // Softer border
            color: 'inherit',
            opacity: 0.9
        };
    }
}


/**
 * Format date as "DD일"
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
    if (isLoading) {
        return (
            <Card>
                <CardHeader className="pb-2">
                    <CardTitle className="text-lg">📅 이번 주 계획</CardTitle>
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
        // Sort: Actual first, then Planned
        dayEvents.sort((a, b) => (Number(b.is_actual || 0) - Number(a.is_actual || 0)));

        days.push({
            date: dateStr,
            dayName: DAY_NAMES[i],
            events: dayEvents
        });
    }

    return (
        <Card>
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">📅 이번 주 현황</CardTitle>
                    <div className="flex gap-4 text-xs">
                        <div className="bg-primary/10 px-2 py-1 rounded">
                            <span className="text-muted-foreground mr-1">계획 TSS</span>
                            <span className="font-bold">{calendar.planned_tss}</span>
                        </div>
                        <div className="bg-green-500/10 px-2 py-1 rounded text-green-700 dark:text-green-400">
                            <span className="mr-1">완료 TSS</span>
                            <span className="font-bold">{calendar.actual_tss}</span>
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
                            className={`text-center p-2 rounded-lg min-h-24 cursor-pointer transition-all hover:bg-muted/80 ${isToday(day.date) ? 'bg-primary/5 ring-1 ring-primary' : 'bg-muted/30'
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
                                        className="text-[10px] p-1 rounded text-left truncate leading-tight shadow-sm"
                                        style={getEventStyle(event)}
                                        title={`${event.name}\n${event.is_actual ? '✅ 완료' : '📅 계획'}`}
                                    >
                                        <div className="flex items-center gap-1">
                                            <span>{getEventIcon(event)}</span>
                                            <span className="truncate flex-1">
                                                {event.name
                                                    .replace("[AICoach]", "")
                                                    .replace("AI Generated - ", "")
                                                    .trim()}
                                            </span>
                                        </div>
                                        {event.tss ? (
                                            <div className="mt-0.5 opacity-80 text-[9px]">
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
            </CardContent>
        </Card>
    );
}
