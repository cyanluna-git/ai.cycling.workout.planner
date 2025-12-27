import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { WeeklyCalendarData, WeeklyEvent } from "@/lib/api";

interface WeeklyCalendarCardProps {
    calendar: WeeklyCalendarData | null;
    isLoading: boolean;
    onSelectDate?: (date: string) => void;
}

const DAY_NAMES = ['월', '화', '수', '목', '금', '토', '일'];

/**
 * Get workout type color
 */
function getWorkoutColor(type: string | null): string {
    if (!type) return '#888';
    const t = type.toLowerCase();
    if (t.includes('ride') || t.includes('virtual')) return '#0ea5e9';
    if (t.includes('run')) return '#f97316';
    if (t.includes('swim')) return '#22c55e';
    return '#8b5cf6';
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
        days.push({
            date: dateStr,
            dayName: DAY_NAMES[i],
            events: dayEvents
        });
    }

    return (
        <Card>
            <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center justify-between">
                    <span>📅 이번 주 계획</span>
                    <span className="text-sm font-normal text-muted-foreground">
                        {calendar.events.length}개 워크아웃
                    </span>
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-7 gap-1">
                    {days.map((day) => (
                        <div
                            key={day.date}
                            onClick={() => onSelectDate?.(day.date)}
                            className={`text-center p-2 rounded-lg min-h-20 cursor-pointer transition-colors hover:bg-muted/80 ${isToday(day.date) ? 'bg-primary/10 ring-2 ring-primary' : 'bg-muted/50'
                                }`}
                        >
                            <div className="text-xs text-muted-foreground mb-1">{day.dayName}</div>
                            <div className={`text-sm font-bold mb-2 ${isToday(day.date) ? 'text-primary' : ''}`}>
                                {formatDate(day.date)}
                            </div>
                            {day.events.map((event) => (
                                <div
                                    key={event.id}
                                    className="text-xs p-1 rounded mb-1 truncate"
                                    style={{
                                        backgroundColor: `${getWorkoutColor(event.workout_type)}20`,
                                        borderLeft: `3px solid ${getWorkoutColor(event.workout_type)}`
                                    }}
                                    title={`${event.name}${event.duration_minutes ? ` • ${event.duration_minutes}분` : ''}${event.tss ? ` • TSS ${event.tss}` : ''}`}
                                >
                                    <div className="font-medium truncate" style={{ color: getWorkoutColor(event.workout_type) }}>
                                        {event.workout_type || 'Workout'}
                                    </div>
                                    {event.duration_minutes && (
                                        <div className="text-muted-foreground">{event.duration_minutes}분</div>
                                    )}
                                </div>
                            ))}
                            {day.events.length === 0 && (
                                <div className="text-xs text-muted-foreground">-</div>
                            )}
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
