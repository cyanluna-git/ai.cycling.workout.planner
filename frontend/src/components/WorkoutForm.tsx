import { useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Bike, Crosshair, Smile, Dumbbell, Flame } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import type { WorkoutGenerateRequest } from "@/lib/api";

interface WorkoutFormProps {
    onGenerate: (request: WorkoutGenerateRequest) => void;
    isLoading: boolean;
}

export function WorkoutForm({ onGenerate, isLoading }: WorkoutFormProps) {
    const { t } = useTranslation();
    const [duration, setDuration] = useState(60);
    const [intensity, setIntensity] = useState("auto");
    const [indoor, setIndoor] = useState(false);

    const INTENSITIES: { value: string; label: string; icon: ReactNode }[] = [
        { value: "auto", label: t('workout.intensityAuto'), icon: <Crosshair className="h-3.5 w-3.5" /> },
        { value: "easy", label: t('workout.intensityEasy'), icon: <Smile className="h-3.5 w-3.5" /> },
        { value: "moderate", label: t('workout.intensityModerate'), icon: <Dumbbell className="h-3.5 w-3.5" /> },
        { value: "hard", label: t('workout.intensityHard'), icon: <Flame className="h-3.5 w-3.5" /> },
    ];

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onGenerate({
            duration,
            style: "auto",
            intensity,
            notes: "",
            indoor,
        });
    };

    return (
        <Card className="w-full">
            <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                    <Bike className="h-5 w-5" /> {t('workout.todayTitle')}
                </CardTitle>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Duration Slider - Compact */}
                    <div className="space-y-2">
                        <div className="flex items-center justify-between">
                            <Label className="text-sm">{t('workout.duration')}</Label>
                            <span className="text-sm font-medium">{duration}{t('common.minutes')}</span>
                        </div>
                        <Slider
                            value={[duration]}
                            onValueChange={(v) => setDuration(v[0])}
                            min={30}
                            max={120}
                            step={15}
                            className="w-full"
                        />
                    </div>

                    {/* Intensity Buttons */}
                    <div className="space-y-2">
                        <Label className="text-sm">{t('workout.intensity')}</Label>
                        <div className="grid grid-cols-4 gap-2">
                            {INTENSITIES.map((i) => (
                                <Button
                                    key={i.value}
                                    type="button"
                                    variant={intensity === i.value ? "default" : "outline"}
                                    size="sm"
                                    onClick={() => setIntensity(i.value)}
                                    className="text-xs"
                                >
                                    <span className="inline-flex items-center gap-1">{i.icon} {i.label}</span>
                                </Button>
                            ))}
                        </div>
                    </div>

                    {/* Bottom Row: Indoor + Generate Button */}
                    <div className="flex items-center gap-3 pt-2">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={indoor}
                                onChange={(e) => setIndoor(e.target.checked)}
                                className="rounded"
                            />
                            <span className="text-sm">{t('workout.indoor')}</span>
                        </label>

                        <Button type="submit" className="flex-1" disabled={isLoading}>
                            {isLoading ? t('common.generating') : t('workout.generate')}
                        </Button>
                    </div>
                </form>
            </CardContent>
        </Card>
    );
}
