import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { GeneratedWorkout } from "@/lib/api";
import { WorkoutChart, getZoneColor } from "./WorkoutChart";

interface WorkoutPreviewProps {
    workout: GeneratedWorkout;
    onRegister: () => void;
    isRegistering: boolean;
    ftp?: number;
}

/**
 * Format step with watts calculation
 * Input: "10m 50%"
 * Output: "10m 50% (126w)" with zone color
 */
function formatStepWithWatts(step: string, ftp: number): { text: string; color: string } {
    const match = step.match(/(\d+m)\s+(\d+)%/);
    if (match) {
        const duration = match[1];
        const percent = parseInt(match[2]);
        const watts = Math.round(ftp * percent / 100);
        return {
            text: `${duration} ${percent}% (${watts}w)`,
            color: getZoneColor(percent)
        };
    }
    return { text: step, color: '#888' };
}

export function WorkoutPreview({ workout, onRegister, isRegistering, ftp = 250 }: WorkoutPreviewProps) {
    return (
        <Card className="w-full">
            <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center justify-between">
                    <span>✨ {workout.name.replace("AI Generated - ", "")}</span>
                    <span className="text-sm font-normal text-muted-foreground">
                        {workout.workout_type} • ~{workout.estimated_duration_minutes}분
                        {workout.estimated_tss && ` • TSS ${workout.estimated_tss}`}
                    </span>
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Design Goal / AI Briefing */}
                {workout.design_goal && (
                    <div className="bg-blue-50/50 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900 rounded-lg p-3 text-sm text-blue-800 dark:text-blue-300">
                        <span className="font-semibold mr-1">💡 Coach's Note:</span>
                        {workout.design_goal}
                    </div>
                )}

                {/* Power Profile Chart */}
                <WorkoutChart workoutText={workout.workout_text} />

                {/* Workout Sections */}
                <div className="bg-muted/50 rounded-lg p-4 font-mono text-sm space-y-3">
                    {workout.warmup.length > 0 && (
                        <div>
                            <div className="text-muted-foreground mb-1">Warmup</div>
                            {workout.warmup.map((step, i) => {
                                const formatted = formatStepWithWatts(step, ftp);
                                return (
                                    <div key={i} style={{ color: formatted.color }}>- {formatted.text}</div>
                                );
                            })}
                        </div>
                    )}

                    {workout.main.length > 0 && (
                        <div>
                            <div className="text-muted-foreground mb-1">Main Set</div>
                            {workout.main.map((step, i) => {
                                const formatted = formatStepWithWatts(step, ftp);
                                return (
                                    <div key={i} style={{ color: formatted.color }} className="font-medium">- {formatted.text}</div>
                                );
                            })}
                        </div>
                    )}

                    {workout.cooldown.length > 0 && (
                        <div>
                            <div className="text-muted-foreground mb-1">Cooldown</div>
                            {workout.cooldown.map((step, i) => {
                                const formatted = formatStepWithWatts(step, ftp);
                                return (
                                    <div key={i} style={{ color: formatted.color }}>- {formatted.text}</div>
                                );
                            })}
                        </div>
                    )}
                </div>

                {/* Register Button */}
                <Button
                    onClick={onRegister}
                    className="w-full"
                    disabled={isRegistering}
                >
                    {isRegistering ? "등록 중..." : "📅 Intervals.icu에 등록"}
                </Button>
            </CardContent>
        </Card>
    );
}

