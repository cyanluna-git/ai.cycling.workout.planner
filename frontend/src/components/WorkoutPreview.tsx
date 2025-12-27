import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { GeneratedWorkout } from "@/lib/api";
import { WorkoutChart, getZoneColor } from "./WorkoutChart";

interface WorkoutPreviewProps {
    workout: GeneratedWorkout;
    onRegister: () => void;
    isRegistering: boolean;
    isRegistered?: boolean; // New prop
    ftp?: number;
}

/**
 * Format step with watts calculation
 * Input examples: 
 * - "10m 50%" -> "10m 50% (125w)"
 * - "10m 50% -> 70%" -> "10m 50% (125w) -> 70% (175w)"
 * - "4x (4m 100% / 4m 50%)" -> "4x (4m 100% (250w) / 4m 50% (125w))"
 */
function formatStepWithWatts(step: string, ftp: number): { text: string; color: string } {
    // 1. Determine main color (simple heuristic: highest intensity found)
    let maxPercent = 0;
    const percentMatches = step.match(/(\d+)%/g);
    if (percentMatches) {
        percentMatches.forEach(p => {
            const val = parseInt(p);
            if (val > maxPercent) maxPercent = val;
        });
    }
    const color = maxPercent > 0 ? getZoneColor(maxPercent) : '#888';

    // 2. Replace all "X%" with "X% (Yw)"
    // Regex matches "digits%"
    const text = step.replace(/(\d+)%/g, (_match, p1) => {
        const percent = parseInt(p1);
        const watts = Math.round(ftp * percent / 100);
        return `${percent}% (${watts}w)`;
    });

    return { text, color };
}

export function WorkoutPreview({ workout, onRegister, isRegistering, isRegistered, ftp = 250 }: WorkoutPreviewProps) {
    return (
        <Card className="w-full">
            <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center justify-between">
                    <span>✨ {workout.name.replace("[AICoach]", "").replace("AI Generated - ", "").trim()}</span>
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

                {/* Register Button or Success Message */}
                {isRegistered ? (
                    <div className="w-full bg-green-500/10 text-green-600 font-bold py-2 rounded-md text-center border border-green-200 dark:border-green-900">
                        ✅ 등록 완료!
                    </div>
                ) : (
                    <Button
                        onClick={onRegister}
                        className="w-full"
                        disabled={isRegistering}
                    >
                        {isRegistering ? "등록 중..." : "📅 Intervals.icu에 등록"}
                    </Button>
                )}
            </CardContent>
        </Card>
    );
}

