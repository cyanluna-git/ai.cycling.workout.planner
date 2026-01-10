import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import type { WorkoutGenerateRequest } from "@/lib/api";

interface WorkoutFormProps {
    onGenerate: (request: WorkoutGenerateRequest) => void;
    isLoading: boolean;
}

const INTENSITIES = [
    { value: "auto", label: "자동", emoji: "🎯" },
    { value: "easy", label: "쉽게", emoji: "😌" },
    { value: "moderate", label: "적당히", emoji: "💪" },
    { value: "hard", label: "빡세게", emoji: "🔥" },
];

export function WorkoutForm({ onGenerate, isLoading }: WorkoutFormProps) {
    const [duration, setDuration] = useState(60);
    const [intensity, setIntensity] = useState("auto");
    const [indoor, setIndoor] = useState(false);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onGenerate({
            duration,
            style: "auto", // Style is now in settings for weekly plans
            intensity,
            notes: "", // Removed
            indoor,
        });
    };

    return (
        <Card className="w-full">
            <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                    🚴 오늘의 워크아웃
                </CardTitle>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Duration Slider - Compact */}
                    <div className="space-y-2">
                        <div className="flex items-center justify-between">
                            <Label className="text-sm">시간</Label>
                            <span className="text-sm font-medium">{duration}분</span>
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
                        <Label className="text-sm">강도</Label>
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
                                    {i.emoji} {i.label}
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
                            <span className="text-sm">🏠 실내</span>
                        </label>

                        <Button type="submit" className="flex-1" disabled={isLoading}>
                            {isLoading ? "생성 중..." : "🎯 워크아웃 생성"}
                        </Button>
                    </div>
                </form>
            </CardContent>
        </Card>
    );
}
