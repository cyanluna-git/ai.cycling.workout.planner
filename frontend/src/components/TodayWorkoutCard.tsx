/**
 * Today's Workout Card
 * 
 * Integrated component combining workout generation form and preview.
 * Shows form when no workout, shows preview when workout exists.
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import type { GeneratedWorkout, WorkoutGenerateRequest } from "@/lib/api";
import { WorkoutChart, getZoneColor } from "./WorkoutChart";
import { cleanWorkoutName } from "@/lib/workout-utils";
import { formatWorkoutSections } from "@/lib/format-workout-steps";

interface TodayWorkoutCardProps {
    workout: GeneratedWorkout | null;
    onGenerate: (request: WorkoutGenerateRequest) => void;
    onRegister: () => void;
    isLoading: boolean;
    isRegistering: boolean;
    isRegistered: boolean;
    ftp: number;
    error: string | null;
    success: string | null;
}

function formatStepWithWatts(step: string, ftp: number): { text: string; color: string } {
    let maxPercent = 0;
    const percentMatches = step.match(/(\\d+)%/g);
    if (percentMatches) {
        percentMatches.forEach(p => {
            const val = parseInt(p);
            if (val > maxPercent) maxPercent = val;
        });
    }
    const color = maxPercent > 0 ? getZoneColor(maxPercent) : '#888';
    const text = step.replace(/(\\d+)%/g, (_match, p1) => {
        const percent = parseInt(p1);
        const watts = Math.round(ftp * percent / 100);
        return `${percent}% (${watts}w)`;
    });
    return { text, color };
}

export function TodayWorkoutCard({
    workout,
    onGenerate,
    onRegister,
    isLoading,
    isRegistering,
    isRegistered,
    ftp,
    error,
    success,
}: TodayWorkoutCardProps) {
    const { t } = useTranslation();
    const [duration, setDuration] = useState(60);
    const [intensity, setIntensity] = useState("auto");
    const [indoor, setIndoor] = useState(false);

    const INTENSITIES = [
        { value: "auto", label: t('workout.intensityAuto'), emoji: "🎯" },
        { value: "easy", label: t('workout.intensityEasy'), emoji: "😌" },
        { value: "moderate", label: t('workout.intensityModerate'), emoji: "💪" },
        { value: "hard", label: t('workout.intensityHard'), emoji: "🔥" },
    ];

    const handleGenerate = () => {
        onGenerate({
            duration,
            style: "auto",
            intensity,
            notes: "",
            indoor,
        });
    };

    // Show preview if workout exists
    if (workout) {
        const sections = workout.steps && workout.steps.length > 0
            ? formatWorkoutSections(workout.steps, ftp)
            : null;

        // Debug logging
        console.log('TodayWorkoutCard - workout data:', {
            hasSteps: !!workout.steps,
            stepsLength: workout.steps?.length,
            hasZwoContent: !!workout.zwo_content,
            workoutText: workout.workout_text?.substring(0, 100)
        });

        return (
            <Card className="w-full">
            {/* Empty state with emoji and guidance */}
                <CardHeader className="pb-2">
                    <CardTitle className="text-base sm:text-lg">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                            <span className="truncate">✨ {cleanWorkoutName(workout.name)}</span>
                            <span className="text-xs sm:text-sm font-normal text-muted-foreground whitespace-nowrap">
                                {workout.workout_type} • ~{workout.estimated_duration_minutes}{t('common.minutes')}
                                {workout.estimated_tss && ` • TSS ${workout.estimated_tss}`}
                            </span>
                        </div>
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    {/* Messages */}
                    {error && (
                        <div className="bg-destructive/10 text-destructive p-3 rounded-lg text-sm">
                            ❌ {error}
                        </div>
                    )}
                    {success && !success.includes(t('common.registered')) && (
                        <div className="bg-green-500/10 text-green-600 p-3 rounded-lg text-sm">
                            {success}
                        </div>
                    )}

                    {/* Design Goal */}
                    {workout.design_goal && (
                        <div className="bg-blue-50/50 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900 rounded-lg p-3 text-sm text-blue-800 dark:text-blue-300">
                            <span className="font-semibold mr-1">💡 Coach's Note:</span>
                            {workout.design_goal}
                        </div>
                    )}

                    {/* Power Chart */}
                    {(workout.steps || workout.zwo_content || workout.workout_text) ? (
                        <WorkoutChart
                            workoutText={workout.workout_text}
                            zwoContent={workout.zwo_content}
                            steps={workout.steps}
                            ftp={ftp}
                        />
                    ) : (
                        <div className="bg-muted/50 rounded-lg p-4 text-sm text-muted-foreground text-center">
                            {t('workout.noChartData')}
                        </div>
                    )}

                    {/* Workout Steps */}
                    <div className="bg-muted/50 rounded-lg p-4 font-mono text-xs sm:text-sm space-y-3 max-h-48 overflow-y-auto">
                        {sections ? (
                            <>
                                {sections.warmup.length > 0 && (
                                    <div>
                                        <div className="text-muted-foreground mb-1">Warmup</div>
                                        {sections.warmup.map((step, i) => (
                                            <div key={i} style={{ color: step.color }}>- {step.text}</div>
                                        ))}
                                    </div>
                                )}
                                {sections.main.length > 0 && (
                                    <div>
                                        <div className="text-muted-foreground mb-1">Main Set</div>
                                        {sections.main.map((step, i) => (
                                            <div key={i} style={{ color: step.color }} className="font-medium">- {step.text}</div>
                                        ))}
                                    </div>
                                )}
                                {sections.cooldown.length > 0 && (
                                    <div>
                                        <div className="text-muted-foreground mb-1">Cooldown</div>
                                        {sections.cooldown.map((step, i) => (
                                            <div key={i} style={{ color: step.color }}>- {step.text}</div>
                                        ))}
                                    </div>
                                )}
                            </>
                        ) : (
                            <>
                                {workout.warmup.length > 0 && (
                                    <div>
                                        <div className="text-muted-foreground mb-1">Warmup</div>
                                        {workout.warmup.map((step, i) => {
                                            const formatted = formatStepWithWatts(step, ftp);
                                            return <div key={i} style={{ color: formatted.color }}>- {formatted.text}</div>;
                                        })}
                                    </div>
                                )}
                                {workout.main.length > 0 && (
                                    <div>
                                        <div className="text-muted-foreground mb-1">Main Set</div>
                                        {workout.main.map((step, i) => {
                                            const formatted = formatStepWithWatts(step, ftp);
                                            return <div key={i} style={{ color: formatted.color }} className="font-medium">- {formatted.text}</div>;
                                        })}
                                    </div>
                                )}
                                {workout.cooldown.length > 0 && (
                                    <div>
                                        <div className="text-muted-foreground mb-1">Cooldown</div>
                                        {workout.cooldown.map((step, i) => {
                                            const formatted = formatStepWithWatts(step, ftp);
                                            return <div key={i} style={{ color: formatted.color }}>- {formatted.text}</div>;
                                        })}
                                    </div>
                                )}
                            </>
                        )}
                    </div>

                    {/* Intensity Selection for Re-generate */}
                    <div className="space-y-2">
                        <Label className="text-sm text-muted-foreground">{t('workout.regenIntensityLabel')}</Label>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                            {INTENSITIES.map((i) => (
                                <Button
                                    key={i.value}
                                    type="button"
                                    variant={intensity === i.value ? "default" : "outline"}
                                    onClick={() => setIntensity(i.value)}
                                    className="h-11 sm:h-9 text-xs transition-all active:scale-95"
                                >
                                    {i.emoji} {i.label}
                                </Button>
                            ))}
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col sm:flex-row gap-2">
                        <Button
                            variant="outline"
                            onClick={handleGenerate}
                            disabled={isLoading}
                            className="flex-1 h-11 sm:h-9 transition-all active:scale-95"
                        >
                            {isLoading ? (
                                <>
                                    <span className="animate-spin">⏳</span>
                                    {t('common.generating')}
                                </>
                            ) : (
                                `🔄 ${t('workout.regenerate')}`
                            )}
                        </Button>
                        {isRegistered ? (
                            <div className="flex-1 bg-green-500/10 text-green-600 font-bold py-2 rounded-md text-center border border-green-200 dark:border-green-900 text-sm min-h-[44px] flex items-center justify-center">
                                ✅ {t('common.registered')}
                            </div>
                        ) : (
                            <Button
                                onClick={onRegister}
                                disabled={isRegistering}
                                className="flex-1 h-11 sm:h-9 transition-all active:scale-95"
                            >
                                {isRegistering ? (
                                    <>
                                        <span className="animate-spin">⏳</span>
                                        {t('common.registering')}
                                    </>
                                ) : (
                                    `📅 ${t('workout.register')}`
                                )}
                            </Button>
                        )}
                    </div>
                </CardContent>
            </Card>
        );
    }

    // Show generation form if no workout
    return (
        <Card className="w-full">
            {/* Empty state with emoji and guidance */}
            <CardHeader className="pb-3">
                <CardTitle className="text-lg">{t("workout.todayTitle")}</CardTitle>
            </CardHeader>
            <CardContent className="py-8 text-center">
                <div className="max-w-md mx-auto space-y-4">
                    <div className="text-5xl mb-4">🎯</div>
                    <h3 className="text-xl font-bold">{t("workout.emptyTitle")}</h3>
                    <p className="text-muted-foreground text-sm">
                        {t("workout.emptyDesc")}
                    </p>

                    {/* Messages */}
                    {error && (
                        <div className="bg-destructive/10 text-destructive p-3 rounded-lg text-sm">
                            ❌ {error}
                        </div>
                    )}

                    {/* Duration */}
                    <div className="space-y-2 mt-6">
                        <div className="flex items-center justify-between">
                            <Label className="text-sm">{t("workout.duration")}</Label>
                            <span className="text-sm font-medium">{duration}{t("common.minutes")}</span>
                        </div>
                        <Slider
                            className="touch-none [&_[role=slider]]:h-11 [&_[role=slider]]:w-11 sm:[&_[role=slider]]:h-5 sm:[&_[role=slider]]:w-5"
                            value={[duration]}
                            onValueChange={(v) => setDuration(v[0])}
                            min={30}
                            max={120}
                            step={15}
                        />
                    </div>

                    {/* Intensity Buttons */}
                    <div className="space-y-2">
                        <Label className="text-sm">{t("workout.intensity")}</Label>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                            {INTENSITIES.map((i) => (
                                <Button
                                    key={i.value}
                                    type="button"
                                    variant={intensity === i.value ? "default" : "outline"}
                                    onClick={() => setIntensity(i.value)}
                                    className="h-11 sm:h-9 text-xs transition-all active:scale-95"
                                >
                                    {i.emoji} {i.label}
                                </Button>
                            ))}
                        </div>
                    </div>

                    {/* Bottom Row */}
                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 pt-2">
                        <label className="flex items-center gap-2 cursor-pointer min-h-[44px]">
                            <input
                                type="checkbox"
                                checked={indoor}
                                onChange={(e) => setIndoor(e.target.checked)}
                                className="rounded h-5 w-5"
                            />
                            <span className="text-sm">{t("workout.indoor")}</span>
                        </label>

                        <Button 
                            onClick={handleGenerate} 
                            disabled={isLoading}
                            className="flex-1 h-11 sm:h-9 transition-all active:scale-95"
                        >
                            {isLoading ? (
                                <>
                                    <span className="animate-spin">⏳</span>
                                    {t("common.generating")}
                                </>
                            ) : (
                                t("workout.generate")
                            )}
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
