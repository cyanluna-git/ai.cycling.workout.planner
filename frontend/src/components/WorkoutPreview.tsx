import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { GeneratedWorkout } from "@/lib/api";

interface WorkoutPreviewProps {
    workout: GeneratedWorkout;
    onRegister: () => void;
    isRegistering: boolean;
}

export function WorkoutPreview({ workout, onRegister, isRegistering }: WorkoutPreviewProps) {
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
                {/* Workout Sections */}
                <div className="bg-muted/50 rounded-lg p-4 font-mono text-sm space-y-3">
                    {workout.warmup.length > 0 && (
                        <div>
                            <div className="text-muted-foreground mb-1">Warmup</div>
                            {workout.warmup.map((step, i) => (
                                <div key={i} className="text-green-600">- {step}</div>
                            ))}
                        </div>
                    )}

                    {workout.main.length > 0 && (
                        <div>
                            <div className="text-muted-foreground mb-1">Main Set</div>
                            {workout.main.map((step, i) => (
                                <div key={i} className="text-orange-600 font-medium">- {step}</div>
                            ))}
                        </div>
                    )}

                    {workout.cooldown.length > 0 && (
                        <div>
                            <div className="text-muted-foreground mb-1">Cooldown</div>
                            {workout.cooldown.map((step, i) => (
                                <div key={i} className="text-blue-600">- {step}</div>
                            ))}
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
